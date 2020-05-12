#==============================================================================
# Author: Anh Tran (Andrew)

# MIT License

# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:

# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.

# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.
#==============================================================================
"""
This script will generate a Verilog file that parallelly computes all bits of 
a pseudo-random output for an input seed, accordingly a LFSR generator polynomial.

To generate a good pseudo random, it is recommended to use a maxium-cycle LFSR polynomial.
The list of maximum-cycle LFSR can be found here: 
https://web.archive.org/web/20161007061934/http://courses.cse.tamu.edu/csce680/walker/lfsr_table.pdf
"""

import argparse


def parse_polynomial(gen_poly):
    """ Extract indexes of bit one in the binary representation of the generation polynomial.
        
        Input: polynomial in binary or hex format. Ex: 0b110110 or 0x36
        
        Output: the length of LFSR, and indexes of bit ones
    """
    
    # make sure input polynomial is in binary or hex presentation
    assert gen_poly.startswith('0b') or gen_poly.startswith('0x')
    
    # convert hex presentation to bin presentation
    if gen_poly.startswith('0x'):
        gen_poly = bin(eval(gen_poly))
    
    # make sure input polynomial taps are not all zeros
    assert eval(gen_poly) != 0
    
    bin_str = gen_poly[2:]
    
    lfsr_len = len(bin_str)  # remove '0b'
    
    one_indices = []
    for ii in range(len(bin_str)):
        if (bin_str[ii]=='1'):
            one_indices.append(lfsr_len-1-ii)
    
    return lfsr_len, one_indices    
    

def xor_two_sets(set1, set2):
    """ merge and remove the same elements if any from 2 sets
    """
    
    return (set.union(set1, set2) - set.intersection(set1, set2))

def gen_random(lfsr_len, one_indices, rand_wd):
    """ generate a list of sets where each set consists of the indexes of LFSR elements going to the XOR taps
    """
    
    rand_out = []
    
    cur_sets = [{ii} for ii in range(lfsr_len)]
    
    for ww in range(rand_wd):
        xor_out = set()
        for oo in range(len(one_indices)):
            xor_out = xor_two_sets(xor_out, cur_sets[one_indices[oo]])
        
        #print(xor_out)
        
        for ii in range(lfsr_len-1,0,-1):
            cur_sets[ii] = cur_sets[ii-1]
        
        cur_sets[0] = xor_out    
        rand_out.append(xor_out)
     
    return rand_out
     
def gen_verilog(rand_out, lfsr_len, one_indices, prefix, suffix):
    """ generate the Verilog module file
    """
    
    bin_str = '0b'
    poly_str = ''
    for ii in range(lfsr_len-1,-1,-1):
        if ii in one_indices:
            bin_str += '1'
            poly_str += "x^%d + " %(ii+1)
        else:
            bin_str += '0'
    
    poly_str += '1' # implicit one
    
    if (suffix=="hex"):
        suffix_str = hex(eval(bin_str))
    else:
        suffix_str = bin_str
    
    filename = "%s_rand_%d_%d_%s.v" % (prefix, lfsr_len, len(rand_out), suffix_str)
    
    f=open(filename, 'w')
    
    indent = "    "
    
    code = "/"*80 + "\n"
    code += "///// Generated code. Don't modify! \n"
    code += "///// Author: Anh Tran (Andrew) \n"
    code += "///// This module parallelly computes a %d-bit pseudo random output from %d-bit input seed \n" % (len(rand_out), lfsr_len)
    code += "///// based on the LFSR polynomial: %s \n" % (poly_str)
    code += "/"*80 + "\n"
    
    code += "module %s_rand_%d_%d_%s (\n" % (prefix, lfsr_len, len(rand_out), suffix_str)
    code += "%sinput [%d-1:0]   seed, \n" % (indent, lfsr_len)
    code += "%soutput [%d-1:0]  out\n" % (indent, len(rand_out))
    code += "%s);\n\n" % (indent)
    
    for ww in range(len(rand_out)):
        code += "%sassign out[%d] = seed[%d]" %(indent, ww, list(rand_out[ww])[0])
        for ii in range(1,len(rand_out[ww])):
            code += " ^ seed[%d]" %(list(rand_out[ww])[ii])
            
        code += ";\n"    
    
    code += "\nendmodule\n"
    
    f.write(code)
    
    f.close()        

    print ("Generated file %s" % (filename))
    

def main(): 
    ap = argparse.ArgumentParser()
    ap.add_argument("-g", "--gen_poly", required=True,
        help="generation polynomial in binary representation. For example: 0b110110 (or 0x36) is for x^6 + x^5 + x^3 + x^2 + 1")
    ap.add_argument("-w", "--out_width", required=True, type=int,
        default=16,
        help="the bitwidth of output")    
    ap.add_argument("-p", "--prefix", required=False,
        default="vgen",
        help="prefix of the name of the generated Verilog module")
    ap.add_argument("-s", "--suffix", required=False,
        default="hex",
        help="suffix of the name of the generated Verilog module")
    
    args = vars(ap.parse_args())

    lfsr_len, one_indices = parse_polynomial(gen_poly = args['gen_poly'])

    rand_out = gen_random(lfsr_len, one_indices, args['out_width'])
    
    gen_verilog(rand_out, lfsr_len, one_indices, args['prefix'], args['suffix'])
    
    
if __name__ == '__main__':
    main()    
