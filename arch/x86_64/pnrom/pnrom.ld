OUTPUT_FORMAT("elf32-i386")
OUTPUT_ARCH(i386)
ENTRY(reset_vector)
SECTIONS
{
  . = 0x000f0000;
  .text : { *(.text*) }

  . = 0x000ffff0;
  .reset : { KEEP(*(.reset)) }

  /DISCARD/ : { *(.comment) *(.note*) *(.eh_frame*) }
}
