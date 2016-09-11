import argparse
import subprocess
import re
import json 





def create_clean_covoutput(covorig_fullpath, ignor_list, outputcov_fullpath):

    with open(covorig_fullpath, 'r') as origfp, open(outputcov_fullpath, 'w') as outfp:
        
        uncov_somthing      = re.compile('\\s*-->[TtFf]?\\s+([0-9]+)')
        uncov_condition     = re.compile('((\\s)?)+-->[TtFf]')
        uncov_case          = re.compile('(\\s)*-->(\\s)+[0-9]+(\\s)+case(\\s)+[a-zA-z]+:$')
        uncov_defult        = re.compile('(\\s)*-->(\\s)+[0-9]+(\\s)+default:$')
        filepathe_patt      = re.compile(r'.*(/?[\w]*\.(c|h)):$')

        ignore_default = 'default' in ignor_list
        uncov_count         = 0
        currcodeline_number = 0
        prevcodeline_number = 0

        for line in origfp: 
            
            #
            # Write src file name 
            #
            if filepathe_patt.match(line):
                print('file name: '.format(line))
                if uncov_count > 0:
                    outfp.write('\n\n\n')
                outfp.write(line)
            #
            # First see if line is an uncovered code line
            #
            uncov_match =  uncov_somthing.match(line)
            currcodeline_number = int(uncov_match.group(1))

            if uncov_match:

                uncov_count += 1

                #
                #-->F    283      if (cmd.pbl_size == 0)
                #  -->f 2079c                      !GPRE_FID(vfValid))
                if uncov_condition.match(line):
                    if any(not ignor_line.rstrip() in line.rstrip() for ignor_line in ignor_list):
                        print('Ignore line: {}'.format(line))
                        if line.startswith('-->F') or line.startswith('-->T'):
                            outfp.write('\n')
                        outfp.write(line)
                #
                #-->      50                  default:
                #
                elif uncov_defult.match(line):
                    if ignore_default:
                        continue
                    else:
                        outfp.write('\n {}'.format(line))
                #
                #-->      48                  case mEthContextlessSlowpath_EVENTID: // context i
                #
                elif uncov_case.match(line):
                    #
                    #Keep case from same switch one line after another
                    if currcodeline_number - prevcodeline_number != 1:
                        outfp.write('\n')
                    outfp.write(line)

                prevcodeline_number = currcodeline_number

    return uncov_count


def tstcov(tst_name, tst_srcpath, ignore_list, ouput_path):
   
    p = subprocess.Popen('covbr -u -c1 -dDir tst_srcpath', stdout=subprocess.PIPE)
    out = p.communicate()
    return amountuncov == 0


def main():
    parser = argparse.ArgumentParser(description="Analyze BullsEye Cov test results remove all ignore conditions.")
    parser.add_argument("-i", "--input_jsn_file", type=str, default="cov_input.json", help="Path to json file containing script input args")

    #
    #read input args
    args                                              = parser.parse_args()
    succsess_dict                                     = dict()

    with open(args.input_jsn_file) as cov_args:
        covtests      = json.load(cov_args)
        global_ignore = covtests['Global']['ignore']
        output_dir    = covtests['Global']['output_dir']

        for tstname, testargs in covtests['Tests'].items():
            ignore_list = testargs['ignore'] + global_ignore
            src_path    = testargs['src_path']

            succsess_dict[tstname] = tstcov(tstname, src_path, ignore_list, output_dir)


if __name__ == '__main__':
    #create_clean_covoutput(r'C:\Users\hsreter\Desktop\ethCovWtSrcCode.txt',['if (ptrPinnedData->ccfcPinnedCount >= MAX_PINNED_CCFC)'], r'C:\Users\hsreter\Desktop\testcov.txt') 
    main()