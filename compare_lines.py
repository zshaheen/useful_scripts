"""
Given two files, compare the two line ranges.
"""

def get_offset_for_linenum(file_path, line_number):
    """
    Given a file, get the byte offset for
    the passed in line number.
    """
    with open(file_path) as f:
        offset = 0
        for i, line in enumerate(f):
            if i == line_number:
                return offset
            offset += len(line)
        return offset

file1 = '/global/cscratch1/sd/zshaheen/E3SM_simulations/20180129.DECKv1b_piControl.ne30_oEC.edison/atm_global.txt'
file2 = '/global/cscratch1/sd/zshaheen/new_model_running_01_29_2019/piControl/atm_global.txt'

file1_start, file1_end = 0, 481
file2_start, file2_end = 3661681-7+41000, 3662162-7+41000

if (file1_end - file1_start) != (file2_end - file2_start):
    msg = 'Both file ranges need to be the same: '
    msg += 'you have file1 ({}) and file2({}).'.format(file1_end-file1_start, file2_end-file2_start)
    raise RuntimeError(msg)

f1_offset = get_offset_for_linenum(file1, file1_start)
f2_offset = get_offset_for_linenum(file2, file2_start)
lines_to_read = file1_end - file1_start

with open(file1) as f1:
    with open(file2) as f2:
        f1.seek(f1_offset)
        f2.seek(f2_offset)
        for _ in range(lines_to_read):
            line1 = f1.readline()
            line2 = f2.readline()
            print(line1)
            print(line2)
            if line1 != line2:
                print('The above two lines are different.')

