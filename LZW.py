# coding: iso-8859-15

# 2016-09-03
# Axel Engström, Sci14

# GIF specialised version of the official LZW compression.

#import numpy, could possibly optimise with numpy

def code_to_bin(code, code_size):
    '''
    Converts integer 'code' to binary string without '0b'
    and adds string of zero's to match code_size.

    Help function to LZW_compress().
    '''
    binstring = bin(code)[2:]
    binstring = (code_size - len(binstring))*'0' + binstring
    return binstring

def LZW_compress(index_stream, mincode=3):
    CC = 2**mincode  # Clear Code
    EOT = 2**mincode + 1  # End Of Transmission Code
    codes = [[i] for i in range(2**mincode+2)]  # Code table.
    index_buffer= [index_stream[0]]
    
    code_length = mincode + 1  # Dynamic code length is introduced for extra compression.
    byte_stream = [code_to_bin(CC, code_length)]
    for i in index_stream[1:]:
        new_buffer = index_buffer+[i]
        if new_buffer in codes:
            index_buffer = new_buffer
        else:
            codes.append(new_buffer)
            
            next_code = codes.index(index_buffer)
            next_byte = code_to_bin(next_code, code_length)
            byte_stream.append(next_byte)
            if len(codes) == 4096:  # Maximum size of code table for GIF format
                # To warn decoder that we're reinitializing 'codes'
                byte_stream.append(code_to_bin(CC, code_length))
                codes = [[i] for i in range(2**mincode+2)]
                code_length = mincode + 1
            if len(codes)-1 == 2**code_length:
                # When code 2**code_length - 1 is added, the code_length should increase.
                code_length += 1
            index_buffer = [i]
    next_code = codes.index(index_buffer)  # Append index_buffer since end of stream
    byte_stream.append(code_to_bin(next_code, code_length))
    
    byte_stream.append(code_to_bin(EOT, code_length))  # End Of Transmission

    ### A series of list and string manipulations to get desired output.
    byte_stream = ''.join(byte_stream[::-1])  # Reverse and join.

    # Reverse in order to be read starting from least significant bit.
    byte_stream = byte_stream[::-1]

    # Grab slices of 8 (byte size) and the remaining part.
    byte_stream = [byte_stream[i:i+8] for i in range(0, len(byte_stream), 8)]

    # Reverse for the correct bit order and convert to integers.
    byte_stream = [int(bytestring[::-1],2) for bytestring in byte_stream]
    return byte_stream
