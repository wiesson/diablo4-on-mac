/* Read-only on disk: verify protection transitions on a private DLL mapping. */
typedef unsigned long DWORD;
typedef void *HANDLE;
typedef struct {void *base, *allocation; DWORD allocation_protect, size, state, protect, type;} MBI;
__declspec(dllimport) void *__stdcall LoadLibraryExA(const char *, HANDLE, DWORD);
__declspec(dllimport) DWORD __stdcall VirtualQuery(const void *, MBI *, DWORD);
__declspec(dllimport) int __stdcall VirtualProtect(void *, DWORD, DWORD, DWORD *);
__declspec(dllimport) DWORD __stdcall GetLastError(void);
__declspec(dllimport) HANDLE __stdcall CreateFileA(const char *,DWORD,DWORD,void *,DWORD,DWORD,HANDLE);
__declspec(dllimport) int __stdcall WriteFile(HANDLE,const void *,DWORD,DWORD *,void *);
__declspec(dllimport) HANDLE __stdcall GetStdHandle(DWORD);
__declspec(dllimport) void __stdcall ExitProcess(DWORD);
static HANDLE log;
static void print(const char *s) {DWORD n=0,w=0;while(s[n])n++;WriteFile(log,s,n,&w,0);WriteFile(GetStdHandle((DWORD)-11),s,n,&w,0);}
static void value(const char *label,DWORD n) {char b[]="00000000\r\n";const char *d="0123456789abcdef";for(int i=0;i<8;i++)b[7-i]=d[(n>>(4*i))&15];print(label);print(b);}
void mainCRTStartup(void) {
 log=CreateFileA("C:\\weinkeller-writecopy-probe.log",0x40000000,3,0,2,0x80,0);
 unsigned char *h=LoadLibraryExA("C:\\Program Files (x86)\\Battle.net\\Battle.net.17778\\libcef.dll",0,1);
 if(!h){value("LOAD_ERROR=",GetLastError());ExitProcess(2);}
 /* RVA observed in the actual failing NtProtectVirtualMemory call. */
 unsigned char *p=h+0x097e9000; MBI m; DWORD before=0,old=0,ignored=0;
 if(!VirtualQuery(p,&m,sizeof(m))){value("QUERY_ERROR=",GetLastError());ExitProcess(3);}
 value("INITIAL_PROTECT=",m.protect);value("ALLOCATION_PROTECT=",m.allocation_protect);
 /* Match actual failing call first: image page directly to PAGE_READONLY. */
 if(!VirtualProtect(p,4096,2,&before)){value("RO_ERROR=",GetLastError());ExitProcess(4);}
 value("DIRECT_RO_OLD=",before);
 if(!VirtualProtect(p,4096,4,&old)){value("RW_ERROR=",GetLastError());ExitProcess(5);}
 *(volatile unsigned char *)p=*(volatile unsigned char *)p;
 if(!VirtualProtect(p,4096,2,&old)){value("SECOND_RO_ERROR=",GetLastError());ExitProcess(6);}
 value("RW_WRITE_RO_OLD=",old);
 VirtualProtect(p,4096,before,&ignored);
 ExitProcess(0);
}
