# CMAKE generated file: DO NOT EDIT!
# Generated by "Unix Makefiles" Generator, CMake Version 3.22

# Delete rule output on recipe failure.
.DELETE_ON_ERROR:

#=============================================================================
# Special targets provided by cmake.

# Disable implicit rules so canonical targets will work.
.SUFFIXES:

# Disable VCS-based implicit rules.
% : %,v

# Disable VCS-based implicit rules.
% : RCS/%

# Disable VCS-based implicit rules.
% : RCS/%,v

# Disable VCS-based implicit rules.
% : SCCS/s.%

# Disable VCS-based implicit rules.
% : s.%

.SUFFIXES: .hpux_make_needs_suffix_list

# Command-line flag to silence nested $(MAKE).
$(VERBOSE)MAKESILENT = -s

#Suppress display of executed commands.
$(VERBOSE).SILENT:

# A target that is always out of date.
cmake_force:
.PHONY : cmake_force

#=============================================================================
# Set environment variables for the build.

# The shell in which to execute make rules.
SHELL = /bin/sh

# The CMake executable.
CMAKE_COMMAND = /usr/bin/cmake

# The command to remove a file.
RM = /usr/bin/cmake -E rm -f

# Escaping for special characters.
EQUALS = =

# The top-level source directory on which CMake was run.
CMAKE_SOURCE_DIR = /home/design/IG/label_printer/ptouch-print

# The top-level build directory on which CMake was run.
CMAKE_BINARY_DIR = /home/design/IG/label_printer/ptouch-print/build

# Include any dependencies generated for this target.
include CMakeFiles/ptouch-print.dir/depend.make
# Include any dependencies generated by the compiler for this target.
include CMakeFiles/ptouch-print.dir/compiler_depend.make

# Include the progress variables for this target.
include CMakeFiles/ptouch-print.dir/progress.make

# Include the compile flags for this target's objects.
include CMakeFiles/ptouch-print.dir/flags.make

CMakeFiles/ptouch-print.dir/src/libptouch.c.o: CMakeFiles/ptouch-print.dir/flags.make
CMakeFiles/ptouch-print.dir/src/libptouch.c.o: ../src/libptouch.c
CMakeFiles/ptouch-print.dir/src/libptouch.c.o: CMakeFiles/ptouch-print.dir/compiler_depend.ts
	@$(CMAKE_COMMAND) -E cmake_echo_color --switch=$(COLOR) --green --progress-dir=/home/design/IG/label_printer/ptouch-print/build/CMakeFiles --progress-num=$(CMAKE_PROGRESS_1) "Building C object CMakeFiles/ptouch-print.dir/src/libptouch.c.o"
	/usr/bin/cc $(C_DEFINES) $(C_INCLUDES) $(C_FLAGS) -MD -MT CMakeFiles/ptouch-print.dir/src/libptouch.c.o -MF CMakeFiles/ptouch-print.dir/src/libptouch.c.o.d -o CMakeFiles/ptouch-print.dir/src/libptouch.c.o -c /home/design/IG/label_printer/ptouch-print/src/libptouch.c

CMakeFiles/ptouch-print.dir/src/libptouch.c.i: cmake_force
	@$(CMAKE_COMMAND) -E cmake_echo_color --switch=$(COLOR) --green "Preprocessing C source to CMakeFiles/ptouch-print.dir/src/libptouch.c.i"
	/usr/bin/cc $(C_DEFINES) $(C_INCLUDES) $(C_FLAGS) -E /home/design/IG/label_printer/ptouch-print/src/libptouch.c > CMakeFiles/ptouch-print.dir/src/libptouch.c.i

CMakeFiles/ptouch-print.dir/src/libptouch.c.s: cmake_force
	@$(CMAKE_COMMAND) -E cmake_echo_color --switch=$(COLOR) --green "Compiling C source to assembly CMakeFiles/ptouch-print.dir/src/libptouch.c.s"
	/usr/bin/cc $(C_DEFINES) $(C_INCLUDES) $(C_FLAGS) -S /home/design/IG/label_printer/ptouch-print/src/libptouch.c -o CMakeFiles/ptouch-print.dir/src/libptouch.c.s

CMakeFiles/ptouch-print.dir/src/ptouch-print.c.o: CMakeFiles/ptouch-print.dir/flags.make
CMakeFiles/ptouch-print.dir/src/ptouch-print.c.o: ../src/ptouch-print.c
CMakeFiles/ptouch-print.dir/src/ptouch-print.c.o: CMakeFiles/ptouch-print.dir/compiler_depend.ts
	@$(CMAKE_COMMAND) -E cmake_echo_color --switch=$(COLOR) --green --progress-dir=/home/design/IG/label_printer/ptouch-print/build/CMakeFiles --progress-num=$(CMAKE_PROGRESS_2) "Building C object CMakeFiles/ptouch-print.dir/src/ptouch-print.c.o"
	/usr/bin/cc $(C_DEFINES) $(C_INCLUDES) $(C_FLAGS) -MD -MT CMakeFiles/ptouch-print.dir/src/ptouch-print.c.o -MF CMakeFiles/ptouch-print.dir/src/ptouch-print.c.o.d -o CMakeFiles/ptouch-print.dir/src/ptouch-print.c.o -c /home/design/IG/label_printer/ptouch-print/src/ptouch-print.c

CMakeFiles/ptouch-print.dir/src/ptouch-print.c.i: cmake_force
	@$(CMAKE_COMMAND) -E cmake_echo_color --switch=$(COLOR) --green "Preprocessing C source to CMakeFiles/ptouch-print.dir/src/ptouch-print.c.i"
	/usr/bin/cc $(C_DEFINES) $(C_INCLUDES) $(C_FLAGS) -E /home/design/IG/label_printer/ptouch-print/src/ptouch-print.c > CMakeFiles/ptouch-print.dir/src/ptouch-print.c.i

CMakeFiles/ptouch-print.dir/src/ptouch-print.c.s: cmake_force
	@$(CMAKE_COMMAND) -E cmake_echo_color --switch=$(COLOR) --green "Compiling C source to assembly CMakeFiles/ptouch-print.dir/src/ptouch-print.c.s"
	/usr/bin/cc $(C_DEFINES) $(C_INCLUDES) $(C_FLAGS) -S /home/design/IG/label_printer/ptouch-print/src/ptouch-print.c -o CMakeFiles/ptouch-print.dir/src/ptouch-print.c.s

# Object files for target ptouch-print
ptouch__print_OBJECTS = \
"CMakeFiles/ptouch-print.dir/src/libptouch.c.o" \
"CMakeFiles/ptouch-print.dir/src/ptouch-print.c.o"

# External object files for target ptouch-print
ptouch__print_EXTERNAL_OBJECTS =

ptouch-print: CMakeFiles/ptouch-print.dir/src/libptouch.c.o
ptouch-print: CMakeFiles/ptouch-print.dir/src/ptouch-print.c.o
ptouch-print: CMakeFiles/ptouch-print.dir/build.make
ptouch-print: /usr/lib/x86_64-linux-gnu/libgd.so
ptouch-print: /usr/lib/x86_64-linux-gnu/libpng.so
ptouch-print: /usr/lib/x86_64-linux-gnu/libz.so
ptouch-print: /usr/lib/x86_64-linux-gnu/libjpeg.so
ptouch-print: /usr/lib/x86_64-linux-gnu/libusb-1.0.so
ptouch-print: CMakeFiles/ptouch-print.dir/link.txt
	@$(CMAKE_COMMAND) -E cmake_echo_color --switch=$(COLOR) --green --bold --progress-dir=/home/design/IG/label_printer/ptouch-print/build/CMakeFiles --progress-num=$(CMAKE_PROGRESS_3) "Linking C executable ptouch-print"
	$(CMAKE_COMMAND) -E cmake_link_script CMakeFiles/ptouch-print.dir/link.txt --verbose=$(VERBOSE)

# Rule to build all files generated by this target.
CMakeFiles/ptouch-print.dir/build: ptouch-print
.PHONY : CMakeFiles/ptouch-print.dir/build

CMakeFiles/ptouch-print.dir/clean:
	$(CMAKE_COMMAND) -P CMakeFiles/ptouch-print.dir/cmake_clean.cmake
.PHONY : CMakeFiles/ptouch-print.dir/clean

CMakeFiles/ptouch-print.dir/depend:
	cd /home/design/IG/label_printer/ptouch-print/build && $(CMAKE_COMMAND) -E cmake_depends "Unix Makefiles" /home/design/IG/label_printer/ptouch-print /home/design/IG/label_printer/ptouch-print /home/design/IG/label_printer/ptouch-print/build /home/design/IG/label_printer/ptouch-print/build /home/design/IG/label_printer/ptouch-print/build/CMakeFiles/ptouch-print.dir/DependInfo.cmake --color=$(COLOR)
.PHONY : CMakeFiles/ptouch-print.dir/depend

