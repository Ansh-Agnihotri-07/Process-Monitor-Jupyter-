#define _WIN32_WINNT 0x0501
#include "process_manager.h"
#include <windows.h>
#include <tlhelp32.h>
#include <psapi.h>
#include <map>
#include <string>
#include <algorithm>
#include <cstdlib>
#include <fstream>
#include <sstream>

static bool isProcessCritical(int pid, const std::string &name)
{
    if (pid <= 4)
    {
        return true;
    }
    std::string lowerName = name;
    std::transform(lowerName.begin(), lowerName.end(), lowerName.begin(), ::tolower);
    const char *critical[] = {"system", "csrss.exe", "svchost.exe", "wininit.exe", "services.exe", "smss.exe", "lsass.exe"};
    for (const char *s : critical)
    {
        if (lowerName == s)
        {
            return true;
        }
    }
    return false;
}

static std::map<DWORD, ULONGLONG> prevProcTime;
static ULONGLONG prevSystemTime = 0;

static std::string getTempFileName()
{
    char tempPath[MAX_PATH];
    GetTempPathA(MAX_PATH, tempPath);
    return std::string(tempPath) + "pmcpu_state.tmp";
}

static void saveState()
{
    std::string tempFile = getTempFileName();
    std::ofstream ofs(tempFile);
    ofs << prevSystemTime << "\n";
    for (auto &pair : prevProcTime)
    {
        ofs << pair.first << " " << pair.second << "\n";
    }
    ofs.close();
}

static void loadState()
{
    std::string tempFile = getTempFileName();
    std::ifstream ifs(tempFile);
    if (ifs)
    {
        ifs >> prevSystemTime;
        DWORD pid;
        ULONGLONG time;
        while (ifs >> pid >> time)
        {
            prevProcTime[pid] = time;
        }
        ifs.close();
        DeleteFileA(tempFile.c_str());
    }
}

static ULONGLONG fileTimeToQuad(const FILETIME &ft)
{
    return (static_cast<ULONGLONG>(ft.dwHighDateTime) << 32) | ft.dwLowDateTime;
}

std::vector<Process> listProcesses()
{
    loadState();
    std::vector<Process> procs;
    HANDLE hSnapshot = CreateToolhelp32Snapshot(TH32CS_SNAPPROCESS, 0);
    if (hSnapshot == INVALID_HANDLE_VALUE)
    {
        saveState();
        return procs;
    }

    PROCESSENTRY32 pe32;
    pe32.dwSize = sizeof(PROCESSENTRY32);

    FILETIME idleFt, kernelFt, userFt;
    GetSystemTimes(&idleFt, &kernelFt, &userFt);
    ULONGLONG currentSystemTime = fileTimeToQuad(kernelFt) + fileTimeToQuad(userFt);
    ULONGLONG systemDelta = currentSystemTime - prevSystemTime;

    if (Process32First(hSnapshot, &pe32))
    {
        do
        {
            Process p;
            p.pid = pe32.th32ProcessID;
            p.name = std::string(pe32.szExeFile);
            p.state = "Running";
            p.cpu = 0.0f;
            p.memory = 0.0f;

            HANDLE hProcess = OpenProcess(PROCESS_QUERY_LIMITED_INFORMATION | PROCESS_VM_READ, FALSE, p.pid);
            if (!hProcess)
            {
                hProcess = OpenProcess(PROCESS_QUERY_INFORMATION, FALSE, p.pid);
            }
            if (hProcess)
            {
                PROCESS_MEMORY_COUNTERS pmc;
                if (GetProcessMemoryInfo(hProcess, &pmc, sizeof(pmc)))
                {
                    p.memory = static_cast<float>(pmc.WorkingSetSize) / (1024 * 1024);
                }

                FILETIME createFt, exitFt, pKernelFt, pUserFt;
                if (GetProcessTimes(hProcess, &createFt, &exitFt, &pKernelFt, &pUserFt))
                {
                    ULONGLONG currentProcTime = fileTimeToQuad(pKernelFt) + fileTimeToQuad(pUserFt);

                    if (prevSystemTime > 0 && systemDelta > 0)
                    {
                        auto it = prevProcTime.find(p.pid);
                        if (it != prevProcTime.end())
                        {
                            ULONGLONG procDelta = currentProcTime - it->second;
                            double cpuPercent = (static_cast<double>(procDelta) / static_cast<double>(systemDelta)) * 100.0;
                            if (cpuPercent < 0)
                                cpuPercent = 0;
                            if (cpuPercent > 100)
                                cpuPercent = 100;
                            p.cpu = static_cast<float>(cpuPercent);
                        }
                    }
                    prevProcTime[p.pid] = currentProcTime;
                }
                CloseHandle(hProcess);
            }
            procs.push_back(p);
        } while (Process32Next(hSnapshot, &pe32));
    }
    prevSystemTime = currentSystemTime;
    CloseHandle(hSnapshot);
    saveState();
    return procs;
}

bool killProcess(int pid)
{
    if (pid <= 0)
        return false;

    HANDLE hProcess = OpenProcess(PROCESS_TERMINATE, FALSE, pid);
    if (!hProcess)
    {
        return false;
    }
    BOOL result = TerminateProcess(hProcess, 0);
    CloseHandle(hProcess);
    return result != 0;
}

bool suspendResumeProcess(int pid, bool suspend)
{
    if (pid <= 0)
        return false;

    HANDLE hSnapshot = CreateToolhelp32Snapshot(TH32CS_SNAPTHREAD, 0);
    if (hSnapshot == INVALID_HANDLE_VALUE)
    {
        return false;
    }

    THREADENTRY32 te32;
    te32.dwSize = sizeof(THREADENTRY32);
    bool success = false;

    if (Thread32First(hSnapshot, &te32))
    {
        do
        {
            if (te32.th32OwnerProcessID == pid)
            {
                HANDLE hThread = OpenThread(THREAD_SUSPEND_RESUME, FALSE, te32.th32ThreadID);
                if (hThread)
                {
                    if (suspend)
                    {
                        SuspendThread(hThread);
                    }
                    else
                    {
                        ResumeThread(hThread);
                    }
                    CloseHandle(hThread);
                    success = true;
                }
            }
        } while (Thread32Next(hSnapshot, &te32));
    }

    CloseHandle(hSnapshot);
    return success;
}

bool pauseProcess(int pid)
{
    return suspendResumeProcess(pid, true);
}

bool resumeProcess(int pid)
{
    return suspendResumeProcess(pid, false);
}

bool changePriority(int pid, int value)
{
    if (pid <= 0)
        return false;

    HANDLE hProcess = OpenProcess(PROCESS_SET_INFORMATION, FALSE, pid);
    if (!hProcess)
    {
        return false;
    }

    DWORD priorityClass;
    if (value < 0)
    {
        priorityClass = HIGH_PRIORITY_CLASS;
    }
    else if (value > 0)
    {
        priorityClass = IDLE_PRIORITY_CLASS;
    }
    else
    {
        priorityClass = NORMAL_PRIORITY_CLASS;
    }

    BOOL result = SetPriorityClass(hProcess, priorityClass);
    CloseHandle(hProcess);
    return result != 0;
}
