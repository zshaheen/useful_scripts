"""
Given two files, compare the two line ranges.
"""
import hashlib

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
# Used to print all of the lines in the range.
print_lines = True

file1_start, file1_end = 0, 481
file2_start, file2_end = 3661681-7+41000, 3662162-7+41000


if (file1_end - file1_start) != (file2_end - file2_start):
    msg = 'Both file ranges need to be the same: '
    msg += 'you have file1 ({}) and file2({}).'.format(file1_end-file1_start, file2_end-file2_start)
    raise RuntimeError(msg)

f1_offset = get_offset_for_linenum(file1, file1_start)
f2_offset = get_offset_for_linenum(file2, file2_start)
lines_to_read = file1_end - file1_start

f1_hash = hashlib.md5()
f2_hash = hashlib.md5()

with open(file1) as f1:
    with open(file2) as f2:
        f1.seek(f1_offset)
        f2.seek(f2_offset)

        for _ in range(lines_to_read):
            line1 = f1.readline()
            line2 = f2.readline()
            f1_hash.update(line1)
            f2_hash.update(line2)
            if print_lines:
                print(line1)
                print(line2)
                if line1 != line2:
                    print('The above two lines are different.')

f1_md5 = f1_hash.hexdigest()
f2_md5 = f2_hash.hexdigest()
print('file1 hash {}'.format(f1_md5))
print('file2 hash {}'.format(f2_md5))
msg = 'They are the same.' if f1_md5 == f2_md5 else 'They are different.'
print(msg)
