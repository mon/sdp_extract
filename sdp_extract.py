from os import mkdir
import os
from struct import pack, unpack, calcsize
import sys

HEADER_LEN = 64

# u16 number of entries
# u16 unk1
# 60 byte gap

def unpack_read(fmt, f, endian = '<'):
    fmt = endian + fmt
    size = calcsize(fmt)
    return unpack(fmt, f.read(size))

def pack_write(fmt, f, *args, endian = '<'):
    fmt = endian + fmt
    f.write(pack(fmt, *args))

def save_wav(info, f, header_offset, out_path):
    f.seek(info['offset'] + header_offset)
    data = f.read(info['length'])
    file_len = len(data) + 44
    bytes_per_second = (info['block_align'] * info['bits_per_samp'])//8
    with open(os.path.join(out_path, '{:04d}_{}.wav'.format(info['index'], info['name'])), 'wb') as out:
        out.write(b'RIFF')
        pack_write('I', out, file_len)
        out.write(b'WAVEfmt ')
        pack_write('I', out, 16)
        pack_write('H', out, 0x10) # OKI-ADPCM
        pack_write('H', out, info['channels'])
        pack_write('I', out, info['sample_rate'])
        pack_write('I', out, bytes_per_second)
        pack_write('H', out, info['block_align'])
        pack_write('H', out, info['bits_per_samp'])
        out.write(b'data')
        pack_write('I', out, len(data))
        out.write(data)

def unpack_sdp(path):
    f = open(path, 'rb')
    out_path = path + '_out'
    try:
        mkdir(out_path)
    except FileExistsError:
        pass

    entries, = unpack_read('H', f)
    print('{} entries'.format(entries))
    f.read(2) # unk1
    f.read(60) # gap
    parsed_entries = []
    for _ in range(entries):
        index, block_align, fmt_id, unk3, unk4, offset, length, loop_point, sample_rate, name = \
            unpack_read('IhhiIIIiI32s', f)

        name = name.rstrip(b'\0').decode('utf-8')
        if fmt_id == 4:
            channels = 1
        elif fmt_id == 5:
            channels = 2
        else:
            raise NotImplementedError()

        info = {
            'index' : index,
            'block_align' : block_align,
            'bits_per_samp' : 4,
            'channels' : channels,
            'unk3' : unk3,
            'unk4' : unk4,
            'loop_point' : loop_point,
            'offset' : offset,
            'length' : length,
            'sample_rate' : sample_rate,
            'name' : name,
        }
        parsed_entries.append(info)

    header_offset = f.tell()
    for p in parsed_entries:
        print(p)
        save_wav(p, f, header_offset, out_path)

    f.close()

if __name__ == '__main__':
    if len(sys.argv) < 2:
        print('Usage: sdp_extract.py file1.sdp [file2.sdp ...]')
        exit(1)

    for arg in sys.argv[1:]:
        unpack_sdp(arg)
