#define _GNU_SOURCE
#include <errno.h>
#include <fcntl.h>
#include <openssl/sha.h>
#include <sched.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/mman.h>
#include <sys/socket.h>
#include <sys/stat.h>
#include <sys/types.h>
#include <sys/wait.h>
#include <time.h>
#include <unistd.h>

#define PAYLOAD 288
static unsigned char payload[PAYLOAD];
static volatile unsigned char sink_byte;

static void pin_cpu(int cpu) {
    cpu_set_t set; CPU_ZERO(&set); CPU_SET(cpu, &set);
    if (sched_setaffinity(0, sizeof(set), &set) != 0) { /* best effort */ }
}
static uint64_t ns_now(void) {
    struct timespec ts; clock_gettime(CLOCK_MONOTONIC_RAW, &ts);
    return (uint64_t)ts.tv_sec*1000000000ull + (uint64_t)ts.tv_nsec;
}
static int write_all(int fd, const void *buf, size_t n) {
    const unsigned char *p=buf; while(n){ ssize_t k=write(fd,p,n); if(k<0){if(errno==EINTR)continue;return -1;} p+=k;n-=k;} return 0;
}
static int read_all(int fd, void *buf, size_t n) {
    unsigned char *p=buf; while(n){ ssize_t k=read(fd,p,n); if(k==0)return -1; if(k<0){if(errno==EINTR)continue;return -1;} p+=k;n-=k;} return 0;
}
static void print_result(const char *name, long n, uint64_t dt) {
    double ns=(double)dt/(double)n; printf("%s %.3f %.3f\n", name, ns, 1e9/ns);
}
static void bench_native(long n) {
    unsigned char out[SHA256_DIGEST_LENGTH]; uint64_t t=ns_now();
    for(long i=0;i<n;i++){ SHA256(payload,PAYLOAD,out); sink_byte ^= out[0]; }
    print_result("linux_native_c_sha256",n,ns_now()-t);
}
static void bench_mmap(long n) {
    unsigned char out[SHA256_DIGEST_LENGTH]; unsigned char *m=mmap(NULL,PAYLOAD,PROT_READ|PROT_WRITE,MAP_PRIVATE|MAP_ANONYMOUS,-1,0);
    if(m==MAP_FAILED){perror("mmap");exit(2);} uint64_t t=ns_now();
    for(long i=0;i<n;i++){ memcpy(m,payload,PAYLOAD); SHA256(m,PAYLOAD,out); sink_byte ^= out[0]; }
    print_result("linux_mmap_local_copy_hash",n,ns_now()-t); munmap(m,PAYLOAD);
}
static void bench_tmpfs(long n) {
    char path[128]; snprintf(path,sizeof(path),"/dev/shm/bioos_linux_bench_%d",getpid());
    int fd=open(path,O_CREAT|O_TRUNC|O_RDWR,0600); if(fd<0){perror("open tmpfs");exit(2);} unlink(path);
    if(ftruncate(fd,PAYLOAD)){perror("ftruncate");exit(2);} unsigned char buf[PAYLOAD],out[SHA256_DIGEST_LENGTH];
    uint64_t t=ns_now();
    for(long i=0;i<n;i++){
      if(pwrite(fd,payload,PAYLOAD,0)!=PAYLOAD){perror("pwrite");exit(2);}
      if(pread(fd,buf,PAYLOAD,0)!=PAYLOAD){perror("pread");exit(2);}
      SHA256(buf,PAYLOAD,out); sink_byte ^= out[0];
    }
    print_result("linux_tmpfs_pwrite_pread_hash",n,ns_now()-t); close(fd);
}
static void bench_socketpair(long n) {
    int sv[2]; if(socketpair(AF_UNIX,SOCK_STREAM,0,sv)){perror("socketpair");exit(2);} pid_t pid=fork(); if(pid<0){perror("fork");exit(2);}
    if(pid==0){ pin_cpu(1); close(sv[0]); unsigned char buf[PAYLOAD],out[SHA256_DIGEST_LENGTH]; for(long i=0;i<n;i++){if(read_all(sv[1],buf,PAYLOAD))_exit(3);SHA256(buf,PAYLOAD,out);if(write_all(sv[1],out,sizeof(out)))_exit(4);} _exit(0); }
    pin_cpu(0); close(sv[1]); unsigned char out[SHA256_DIGEST_LENGTH]; uint64_t t=ns_now();
    for(long i=0;i<n;i++){if(write_all(sv[0],payload,PAYLOAD))exit(2);if(read_all(sv[0],out,sizeof(out)))exit(2);sink_byte^=out[0];}
    uint64_t dt=ns_now()-t; close(sv[0]); int st=0; waitpid(pid,&st,0); if(!WIFEXITED(st)||WEXITSTATUS(st))exit(3); print_result("linux_unix_socket_process_hash",n,dt);
}
static void bench_pipe(long n) {
    int req[2],resp[2]; if(pipe(req)||pipe(resp)){perror("pipe");exit(2);} pid_t pid=fork(); if(pid<0){perror("fork");exit(2);}
    if(pid==0){ pin_cpu(1); close(req[1]);close(resp[0]); unsigned char buf[PAYLOAD],out[SHA256_DIGEST_LENGTH]; for(long i=0;i<n;i++){if(read_all(req[0],buf,PAYLOAD))_exit(3);SHA256(buf,PAYLOAD,out);if(write_all(resp[1],out,sizeof(out)))_exit(4);} _exit(0); }
    pin_cpu(0); close(req[0]);close(resp[1]); unsigned char out[SHA256_DIGEST_LENGTH]; uint64_t t=ns_now();
    for(long i=0;i<n;i++){if(write_all(req[1],payload,PAYLOAD))exit(2);if(read_all(resp[0],out,sizeof(out)))exit(2);sink_byte^=out[0];}
    uint64_t dt=ns_now()-t; close(req[1]);close(resp[0]); int st=0; waitpid(pid,&st,0); if(!WIFEXITED(st)||WEXITSTATUS(st))exit(3); print_result("linux_pipe_process_hash",n,dt);
}
static void bench_shared(long n) {
    unsigned char *m=mmap(NULL,PAYLOAD,PROT_READ|PROT_WRITE,MAP_SHARED|MAP_ANONYMOUS,-1,0); if(m==MAP_FAILED){perror("mmap shared");exit(2);} int sv[2]; if(socketpair(AF_UNIX,SOCK_STREAM,0,sv)){perror("socketpair");exit(2);} pid_t pid=fork(); if(pid<0){perror("fork");exit(2);}
    if(pid==0){ pin_cpu(1); close(sv[0]); unsigned char sig,out[SHA256_DIGEST_LENGTH]; for(long i=0;i<n;i++){if(read_all(sv[1],&sig,1))_exit(3);SHA256(m,PAYLOAD,out);if(write_all(sv[1],out,sizeof(out)))_exit(4);} _exit(0); }
    pin_cpu(0); close(sv[1]); unsigned char sig=1,out[SHA256_DIGEST_LENGTH]; uint64_t t=ns_now();
    for(long i=0;i<n;i++){memcpy(m,payload,PAYLOAD);if(write_all(sv[0],&sig,1))exit(2);if(read_all(sv[0],out,sizeof(out)))exit(2);sink_byte^=out[0];}
    uint64_t dt=ns_now()-t; close(sv[0]); int st=0; waitpid(pid,&st,0); if(!WIFEXITED(st)||WEXITSTATUS(st))exit(3); munmap(m,PAYLOAD); print_result("linux_shared_mmap_process_hash",n,dt);
}
int main(int argc,char **argv){ long n=argc>1?strtol(argv[1],NULL,10):50000; if(n<1)return 2; for(int i=0;i<PAYLOAD;i++)payload[i]=(unsigned char)((i*131+17)&255); pin_cpu(0); unsigned char warm[SHA256_DIGEST_LENGTH]; for(int w=0;w<2000;w++) SHA256(payload,PAYLOAD,warm); sink_byte ^= warm[0]; bench_native(n); bench_mmap(n); bench_tmpfs(n); bench_shared(n); bench_pipe(n); bench_socketpair(n); return 0; }
