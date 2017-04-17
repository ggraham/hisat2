#!/usr/bin/env python

#
# Copyright 2017, Daehwan Kim <infphilo@gmail.com>
#
# This file is part of HISAT 2.
#
# HISAT 2 is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# HISAT 2 is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with HISAT 2.  If not, see <http://www.gnu.org/licenses/>.
#


import os, sys, subprocess, re
import inspect, operator
from argparse import ArgumentParser, FileType
import typing_common

# sequences for DNA fingerprinting loci are available at http://www.cstl.nist.gov/biotech/strbase/seq_ref.htm

CODIS_seq = {
    "CSF1PO" :
    # http://www.cstl.nist.gov/biotech/strbase/str_CSF1PO.htm
    # allele 13: 5:150076172-150076490 - (samtools faidx genome.fa - GRCh38)
    ["[AGAT]13",
     "AACCTGAGTCTGCCAAGGACTAGCAGGTTGCTAACCACCCTGTGTCTCAGTTTTCCTACCTGTAAAATGAAGATATTAACAGTAACTGCCTTCATAGATAGAAGATAGATAGATT", # left flanking sequence
     "AGATAGATAGATAGATAGATAGATAGATAGATAGATAGATAGATAGATAGAT", # STR
     "AGGAAGTACTTAGAACAGGGTCTGACACAGGAAATGCTGTCCAAGTGTGCACCAGGAGATAGTATCTGAGAAGGCTCAGTCTGGCACCATGTGGGTTGGGTGGGAACCTGGAGGCTGGAGAATGGGCTGAAGATGGCCAGTGGTGTGTGGAA"], # right flanking sequence
             
    "FGA" :
    # http://www.cstl.nist.gov/biotech/strbase/str_FGA.htm
    # allele 22: 4:154587696-154587891 -
    ["[TTTC]3TTTTTTCT[CTTT]14CTCC[TTCC]2",
     "GCCCCATAGGTTTTGAACTCACAGATTAAACTGTAACCAAAATAAAATTAGGCATATTTACAAGCTAG",
     "TTTCTTTCTTTCTTTTTTCTCTTTCTTTCTTTCTTTCTTTCTTTCTTTCTTTCTTTCTTTCTTTCTTTCTTTCTTTCTCCTTCCTTCC",
     "TTTCTTCCTTTCTTTTTTGCTGGCAATTACAGACAAATCA"],

    "TH01" :
    # http://www.cstl.nist.gov/biotech/strbase/str_TH01.htm
    # allele 7: 11:2170990-2171176 +
    ["[AATG]7",
     "GTGGGCTGAAAAGCTCCCGATTATCCAGCCTGGCCCACACAGTCCCCTGTACACAGGGCTTCCGAGTGCAGGTCACAGGGAACACAGACTCCATGGTG",
     "AATGAATGAATGAATGAATGAATGAATG",
     "AGGGAAATAAGGGAGGAACAGGCCAATGGGAATCACCCCAGAGCCCAGATACCCTTTGAAT"],
             
    "TPOX" :
    # http://www.cstl.nist.gov/biotech/strbase/str_TPOX.htm
    # allele 8: 2:1489617-1489848
    ["[AATG]8",
     "ACTGGCACAGAACAGGCACTTAGGGAACCCTCACTG",
     "AATGAATGAATGAATGAATGAATGAATGAATG",
     "TTTGGGCAAATAAACGCTGACAAGGACAGAAGGGCCTAGCGGGAAGGGAACAGGAGTAAGACCAGCGCACAGCCCGACTTGTGTTCAGAAGACCTGGGATTGGACCTGAGGAGTTCAATTTTGGATGAATCTCTTAATTAACCTGTGGGGTTCCCAGTTCCTCC"],
             
    "VWA" :
    # http://www.cstl.nist.gov/biotech/strbase/str_VWA.htm
    # allele unknown: 12:5983938-5984087 -
    ["TCTA[TCTG]5[TCTA]11TCCATCTA",
     "CCCTAGTGGATGATAAGAATAATCAGTATGTGACTTGGATTGA",
     "TCTATCTGTCTGTCTGTCTGTCTGTCTATCTATCTATCTATCTATCTATCTATCTATCTATCTATCTATCCATCTA",
     "TCCATCCATCCTATGTATTTATCATCTGTCC"],
             
    "D3S1358" :
    # http://www.cstl.nist.gov/biotech/strbase/str_D3S1358.htm
    # allele unknown: 3:45540713-45540843 +
    ["TCTATCTG[TCTA]14",
     "ATGAAATCAACAGAGGCTTGCATGTA",
     "TCTATCTGTCTATCTATCTATCTATCTATCTATCTATCTATCTATCTATCTATCTATCTATCTA",
     "TGAGACAGGGTCTTGCTCTGTCACCCAGATTGGACTGCAGT"],
             
    "D5S818" :
    # http://www.cstl.nist.gov/biotech/strbase/str_D5S818.htm
    # allele 11: 5:123775504-123775638 -
    ["[AGAT]11",
     "GGTGATTTTCCTCTTTGGTATCCTTATGTAATATTTTGA",
     "AGATAGATAGATAGATAGATAGATAGATAGATAGATAGATAGAT",
     "AGAGGTATAAATAAGGATACAGATAAAGATACAAATGTTGTAAACTGTGGCT"],
             
    "D7S820" :
    # http://www.cstl.nist.gov/biotech/strbase/str_D7S820.htm
    # allele 13: 7:84160125-84160367 -
    ["[GATA]13",
     "ATGTTGGTCAGGCTGACTATGGAGTTATTTTAAGGTTAATATATATAAAGGGTATGATAGAACACTTGTCATAGTTTAGAACGAACTAAC",
     "GATAGATAGATAGATAGATAGATAGATAGATAGATAGATAGATAGATAGATA",
     "GACAGATTGATAGTTTTTTTTAATCTCACTAAATAGTCTATAGTAAACATTTAATTACCAATATTTGGTGCAATTCTGTCAATGAGGATAAATGTGGAATC"],
             
    "D8S1179" :
    # http://www.cstl.nist.gov/biotech/strbase/str_D8S1179.htm
    # allele 13: 8:124894838-124895018 +
    ["[TCTA]1[TCTG]1[TCTA]11",
     "TTTTTGTATTTCATGTGTACATTCGTA",
     "TCTATCTGTCTATCTATCTATCTATCTATCTATCTATCTATCTATCTATCTA",
     "TTCCCCACAGTGAAAATAATCTACAGGATAGGTAAATAAATTAAGGCATATTCACGCAATGGGATACGATACAGTGATGAAAATGAACTAATTATAGCTACG"],
             
    "D13S317" :
    # http://www.cstl.nist.gov/biotech/strbase/str_D13S317.htm
    # Perhaps, allele 11: 13:82147921-82148112 +
    ["[TATC]11",
     "ATCACAGAAGTCTGGGATGTGGAGGAGAGTTCATTTCTTTAGTGGGCATCCGTGACTCTCTGGACTCTGACCCATCTAACGCCTATCTGTATTTACAAATACAT",
     "TATCTATCTATCTATCTATCTATCTATCTATCTATCTATCTATC",
     "AATCAATCATCTATCTATCTTTCTGTCTGTCTTTTTGGGCTGCC"],
             
    "D16S539" :
    # http://www.cstl.nist.gov/biotech/strbase/str_D16S539.htm
    # allele 11: 16:86352518-86352805 +
    ["[GATA]11",
     "GGGGGTCTAAGAGCTTGTAAAAAGTGTACAAGTGCCAGATGCTCGTTGTGCACAAATCTAAATGCAGAAAAGCACTGAAAGAAGAATCCAGAAAACCACAGTTCCCATTTTTATATGGGAGCAAACAAAGGCAGATCCCAAGCTCTTCCTCTTCCCTAGATCAATACAGACAGACAGACAGGTG",
     "GATAGATAGATAGATAGATAGATAGATAGATAGATAGATAGATA",
     "TCATTGAAAGACAAAACAGAGATGGATGATAGATACATGCTTACAGATGCACACACAAAC"],
             
    "D18S51" :
    # http://www.cstl.nist.gov/biotech/strbase/str_D18S51.htm
    # allele 18: 18:63281611-63281916 +
    ["[AGAA]18",
     "GAGCCATGTTCATGCCACTGCACTTCACTCTGAGTGACAAATTGAGACCTTGTCTC",
     "AGAAAGAAAGAAAGAAAGAAAGAAAGAAAGAAAGAAAGAAAGAAAGAAAGAAAGAAAGAAAGAAAGAAAGAA",
     "AAAGAGAGAGGAAAGAAAGAGAAAAAGAAAAGAAATAGTAGCAACTGTTATTGTAAGACATCTCCACACACCAGAGAAGTTAATTTTAATTTTAACATGTTAAGAACAGAGAGAAGCCAACATGTCCACCTTAGGCTGACGGTTTGTTTATTTGTGTTGTTGCTGGTAGTCGGGTTTG"],
             
    "D21S11" :
    # http://www.cstl.nist.gov/biotech/strbase/str_D21S11.htm
    # Perhaps, allele 29: 21:19181945-19182165 +
    ["[TCTA]4[TCTG]6[TCTA]3TA[TCTA]3TCA[TCTA]2TCCATA[TCTA]11",
     "GTGAGTCAATTCCCCAAGTGAATTGCCT",
     "TCTATCTATCTATCTATCTGTCTGTCTGTCTGTCTGTCTGTCTATCTATCTATATCTATCTATCTATCATCTATCTATCCATATCTATCTATCTATCTATCTATCTATCTATCTATCTATCTATCTA",
     "TCGTCTATCTATCCAGTCTATCTACCTCCTATTAGTCTGTCTCTGGAGAACATTGACTAATACAAC"]
}

# "AMEL" - http://www.cstl.nist.gov/biotech/strbase/jpg_amel.htm
#          X chromosome has 6 bp deletion and Y chromosome doesn't

CODIS_ref_name = {}


"""
## Download variant information from website
"""
def get_html(url):
    download_cmd = ["wget",
                    "-O", "-",
                    url]
    proc = subprocess.Popen(download_cmd,
                            stdout=subprocess.PIPE,
                            stderr=open("/dev/null", 'w'))

    output = ""
    for line in proc.stdout:
        output += line

    return output


"""
"""
def get_flanking_seqs(ex_path,
                      seq,
                      flank_len = 500):
    def align_seq(ex_path, seq):
        hisat2 = os.path.join(ex_path, "../hisat2")
        aligner_cmd = [hisat2,
                       "--score-min", "C,0",
                       "--no-unal",
                        "-x", "grch38/genome",
                        "-c", seq]
        align_proc = subprocess.Popen(aligner_cmd,
                                      stdout=subprocess.PIPE,
                                      stderr=open("/dev/null", 'w'))
        chr, left, right, strand = "", -1, -1, '+'
        for line in align_proc.stdout:
            if line.startswith('@'):
                continue
            line = line.strip()
            cols = line.split()
            allele_id, flag, chr, left, _, cigar_str = cols[:6]
            assert cigar_str[-1] == 'M'
            left = int(left)
            flag = int(flag)
            strand = '-' if flag & 0x10 else '+'
            assert cigar_str == ("%dM" % len(seq))
            right = left + len(seq)
            break
        
        assert chr != "" and left >= 0 and right > left
        return chr, left, right, strand
    
    chr, left, right, strand = align_seq(ex_path, seq)    
    left_flank_seq, right_flank_seq = "", ""
    if left > 1:
        extract_seq_cmd = ["samtools", "faidx", "genome.fa", "%s:%d-%d" % (chr, max(1, left - flank_len), left - 1)]
        extract_seq_proc = subprocess.Popen(extract_seq_cmd,
                                            stdout=subprocess.PIPE,
                                            stderr=open("/dev/null", 'w'))
        for line in extract_seq_proc.stdout:
            if line.startswith('>'):
                continue
            line = line.strip()
            left_flank_seq += line
    extract_seq_cmd = ["samtools", "faidx", "genome.fa", "%s:%d-%d" % (chr, right, right + flank_len - 1)]
    extract_seq_proc = subprocess.Popen(extract_seq_cmd,
                                        stdout=subprocess.PIPE,
                                        stderr=open("/dev/null", 'w'))
    for line in extract_seq_proc.stdout:
        if line.startswith('>'):
            continue
        line = line.strip()
        right_flank_seq += line

    if strand == '-':
        left_flank_seq, right_flank_seq = typing_common.reverse_complement(right_flank_seq), typing_common.reverse_complement(left_flank_seq)

    chr, _, _, _ = align_seq(ex_path, left_flank_seq + seq + right_flank_seq)
    assert chr != ""
    
    return left_flank_seq, right_flank_seq


"""
Extract multiple sequence alignments
"""
def extract_msa(base_dname,
                base_fname,
                verbose):    

    # Current script directory
    curr_script = os.path.realpath(inspect.getsourcefile(extract_msa))
    ex_path = os.path.dirname(curr_script)

    # Download human genome and HISAT2 index
    HISAT2_fnames = ["grch38",
                     "genome.fa",
                     "genome.fa.fai"]
    if not typing_common.check_files(HISAT2_fnames):
        typing_common.download_genome_and_index(ex_path)

    # Add some additional sequences to allele sequences to make them reasonably long for typing and assembly
    for locus_name, fields in CODIS_seq.items():
        _, left_seq, repeat_seq, right_seq = fields
        allele_seq = left_seq + repeat_seq + right_seq
        left_flank_seq, right_flank_seq = get_flanking_seqs(ex_path, allele_seq)
        CODIS_seq[locus_name][1] = left_flank_seq + left_seq
        CODIS_seq[locus_name][3] = right_seq + right_flank_seq

        print >> sys.stderr, "%s is found on the reference genome (GRCh38)" % locus_name
    
    # CODIS database base URL
    base_url = "http://www.cstl.nist.gov/biotech/strbase"
    
    # Refer to Python's regular expression at https://docs.python.org/2/library/re.html
    #   <td width="16%" align="center"><font size="4">47.2 </font> </td>
    allele_re = re.compile('>(\d+\.?\d?\"?\'*\(?\d*\.?\d?\"?\'*\)?\*?)</')
    #   <td width="35%"><font size="2">[TTTC]<sub>4</sub>TTTT TT<span style="mso-spacerun: yes"> </span>[CTTT]<sub>14</sub>[CTGT]<sub>3</sub>[CTTT]<sub>14 </sub>[CTTC]<sub>4</sub>[CTTT]<sub>3</sub>CTCC[TTCC]<sub>4</sub></font> </td>
    # repeat_re = re.compile('^(\[[ACGT]+\]\d+|[ACGT]+)+$')
    repeat_re = re.compile('^(\[[ACGT]+\]\d+|[ACGT]+)+$')
    # Remove extra tags
    tag_re = re.compile('(<[^>]*>)')
    nbsp_re = re.compile('&nbsp;')
    quot_re = re.compile('&quot;')
    for locus_name in CODIS_seq.keys():
        url = "%s/str_%s.htm" % (base_url, locus_name)
        content = get_html(url).split("\r\n")
        content = map(lambda x: x.strip().replace(' ',''), content)
        content2 = []
        for line in content:
            if line.startswith("<t") or \
               line.startswith("</tr") or \
               len(content2) == 0:
                content2.append(line)
            else:
                content2[-1] += line

        content = content2
        alleles = []
        l = 0
        while l < len(content):
            line = content[l]
            if line.startswith("<tr"):
                l += 1
                if l < len(content):
                    line = content[l]
                    line = re.sub(nbsp_re, '', line)
                    line = re.sub(quot_re, "''", line)
                    allele_match = allele_re.search(line)
                    if not allele_match:
                        continue
                    allele_id = allele_match.group(1)
                    l += 1
                    repeat_match = None
                    while l < len(content):
                        line = content[l]                        
                        if not line.startswith("<td"):
                            break
                        line = re.sub(tag_re, '', line)
                        line = re.sub(nbsp_re, '', line)
                        repeat_match = repeat_re.search(line)
                        if repeat_match:
                            break
                        l += 1
                        
                    if not repeat_match:
                        continue

                    repeat_st = line
                    alleles.append([allele_id, repeat_st])
            else:
                l += 1

        if len(alleles) <= 0:
            continue

        # From   [TTTC]3TTTTTTCT[CTTT]20CTCC[TTCC]2
        # To     [['TTTC', 3], ['TTTTTTCT', 1], ['CTTT', 20], ['CTCC', 1], ['TTCC', 2]]
        def read_allele(repeat_st):
            allele = []
            s = 0
            while s < len(repeat_st):
                ch = repeat_st[s]
                assert ch in "[ACGT"
                if ch == '[':
                    s += 1
                    repeat = ""
                    while s < len(repeat_st):
                        nt = repeat_st[s]
                        if nt in "ACGT":
                            repeat += nt
                            s += 1
                        else:
                            assert nt == ']'
                            s += 1
                            break
                    assert s < len(repeat_st)
                    num = 0
                    while s < len(repeat_st):
                        digit = repeat_st[s]
                        if digit.isdigit():
                            num = num * 10 + int(digit)
                            s += 1
                        else:
                            break
                    assert num > 0
                    allele.append([repeat, num])
                else:
                    repeat = ""
                    while s < len(repeat_st):
                        nt = repeat_st[s]
                        if nt in "ACGT":
                            repeat += nt
                            s += 1
                        else:
                            assert nt == '['
                            break
                    allele.append([repeat, 1])

            # Sanity check
            cmp_repeat_st = ""
            for repeat, repeat_num in allele:
                if repeat_num > 1 or locus_name == "D8S1179":
                    cmp_repeat_st += "["
                cmp_repeat_st += repeat
                if repeat_num > 1 or locus_name == "D8S1179":
                    cmp_repeat_st += "]%d" % repeat_num
                        
            assert repeat_st == cmp_repeat_st                        
            return allele

        alleles = [[allele_id, read_allele(repeat_st)] for allele_id, repeat_st in alleles]

        def to_sequence(repeat_st):
            sequence = ""
            for repeat, repeat_num in repeat_st:
                sequence += (repeat * repeat_num)
            return sequence

        allele_seqs = [[allele_id, to_sequence(repeat_st)] for allele_id, repeat_st in alleles]
        _, ref_allele_left, ref_allele, ref_allele_right = CODIS_seq[locus_name]
        for allele_id, allele_seq in allele_seqs:
            if ref_allele == allele_seq:
                CODIS_ref_name[locus_name] = allele_id
                break
        if locus_name not in CODIS_ref_name:
            CODIS_ref_name[locus_name] = "GRCh38"
            # Add GRCh38 allele
            allele_seqs = [["GRCh38" % locus_name, ref_allele]] + allele_seqs

        print >> sys.stderr, "%s: %d alleles with reference allele as %s" % (locus_name, len(alleles), CODIS_ref_name[locus_name])
        if verbose:
            print >> sys.stderr, "\t", ref_allele_left, ref_allele, ref_allele_right
            for allele_id, allele in alleles:
                print >> sys.stderr, allele_id, "\t", allele

        ### Perform ClustalW multiple sequence alignment

        # Create a temporary allele sequence file
        seq_fname = "%s.tmp.fa" % locus_name
        msf_fname = "%s.tmp.aln" % locus_name
        dnd_fname = "%s.tmp.dnd" % locus_name
        seq_file = open(seq_fname, 'w')
        for allele_id, allele_seq in allele_seqs:
            print >> seq_file, ">%s" % allele_id
            print >> seq_file, allele_seq
        seq_file.close()

        # Run ClustalW - see http://www.clustal.org/clustal2 for more details
        clustalw_cmd = ["clustalw2", seq_fname]
        try:
            clustalw_proc = subprocess.Popen(clustalw_cmd,
                                             stdout=open("/dev/null", 'w'),
                                             stderr=open("/dev/null", 'w'))
            clustalw_proc.communicate()
            if not os.path.exists(msf_fname):
                print >> sys.stderr, "Error: running ClustalW failed."
        except:
            print >> sys.stderr, "Error: please install the latest version of ClustalW."

        allele_dic = {}
        for allele_id, allele_seq in allele_seqs:
            allele_dic[allele_id] = allele_seq

        allele_repeat_msf = {}
        for line in open(msf_fname):
            line = line.strip()
            if len(line) == 0 or \
               line.startswith("CLUSTAL") or \
               line.startswith("*"):
                continue
            
            tmp_allele_id, repeat = line.split()
            # ClustalW sometimes changes allele names
            allele_id = ""
            parenthesis_open = True
            for ch in tmp_allele_id:
                if ch == '_':
                    if parenthesis_open:
                        allele_id += '('
                    else:
                        allele_id += ')'
                    parenthesis_open = not parenthesis_open
                else:
                    allele_id += ch
            assert parenthesis_open
            repeat = repeat.replace('-', '.')
            if allele_id not in allele_repeat_msf:
                allele_repeat_msf[allele_id] = repeat
            else:
                allele_repeat_msf[allele_id] += repeat

        # Sanity check
        assert len(allele_dic) == len(allele_repeat_msf)
        repeat_len = -1
        for repeat_msf in allele_repeat_msf.values():
            if repeat_len < 0:
                repeat_len = len(repeat_msf)
            else:
                assert repeat_len == len(repeat_msf)

        # Creat full multiple sequence alignment
        ref_allele_id = CODIS_ref_name[locus_name]
        allele_msf = {}
        for allele_id, repeat_msf in allele_repeat_msf.items():
            allele_msf[allele_id] = ref_allele_left + repeat_msf + ref_allele_right
            
        os.remove(seq_fname)
        os.remove(msf_fname)
        os.remove(dnd_fname)

        # Make sure the length of allele ID is short, less than 20 characters
        max_allele_id_len = max([len(allele_id) for allele_id in allele_dic.keys()])
        assert max_allele_id_len < 20

        # Write MSF (multiple sequence alignment file)
        msf_len = len(ref_allele_left) + len(ref_allele_right) + repeat_len
        msf_fname = "%s_gen.msf" % locus_name
        msf_file = open(msf_fname, 'w')
        for s in range(0, msf_len, 50):
            for allele_id, msf in allele_msf.items():
                assert len(msf) == msf_len
                allele_name = "%s*%s" % (locus_name, allele_id)
                print >> msf_file, "%20s" % allele_name,
                for s2 in range(s, min(msf_len, s + 50), 10):
                    print >> msf_file, " %s" % msf[s2:s2+10],
                print >> msf_file
                
            if s + 50 >= msf_len:
                break
            print >> msf_file

        msf_file.close()


        # Write FASTA file
        fasta_fname = "%s_gen.fasta" % locus_name
        fasta_file = open(fasta_fname, 'w')
        for allele_id, allele_seq in allele_seqs:
            gen_seq = ref_allele_left + allele_seq + ref_allele_right
            print >> fasta_file, ">%s*%s %d bp" % (locus_name, allele_id, len(gen_seq))
            for s in range(0, len(gen_seq), 60):
                print >> fasta_file, gen_seq[s:s+60]
        fasta_file.close()


"""
"""
if __name__ == '__main__':
    parser = ArgumentParser(
        description="Extract multiple sequence alignments for DNA Fingerprinting loci")
    parser.add_argument("-b", "--base",
                        dest="base_fname",
                        type=str,
                        default="codis",
                        help="base filename (default: codis)")
    parser.add_argument("-v", "--verbose",
                        dest="verbose",
                        action="store_true",
                        help="also print some statistics to stderr")

    args = parser.parse_args()
    if args.base_fname.find('/') != -1:
        elems = args.base_fname.split('/')
        base_fname = elems[-1]
        base_dname = '/'.join(elems[:-1])
    else:
        base_fname = args.base_fname
        base_dname = ""
        
    extract_msa(base_dname,
                base_fname,                
                args.verbose)
