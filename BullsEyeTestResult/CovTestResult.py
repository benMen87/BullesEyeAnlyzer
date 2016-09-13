import argparse
import subprocess
import re
import json 





def create_clean_covoutput(orig_uncov, ignor_list, outputcov_fullpath):

    with open(outputcov_fullpath, 'w') as outfp:
        
        uncov_somthing      = re.compile('\\s*-->[TtFf]?\\s+([0-9]+)\\s+([(_A-za-z].*)')
        uncov_condition     = re.compile('\\s*-->[TtFf]\\s+[0-9]+[a-z]?\\s+([(_A-za-z].*)')
        uncov_case          = re.compile('\\s*-->\\s+[0-9]+\\s+(case\\s+[a-zA-z]+):$')
        uncov_defult        = re.compile('(\\s)*-->(\\s)+[0-9]+(\\s)+default:$')
        filepathe_patt      = re.compile(r'.*(/?[\w]*\.(c|h)):$')

        ignore_default = 'default' in ignor_list
        uncov_count         = 0
        currcodeline_number = 0
        prevcodeline_number = 0


        new_srcfile = False
        for line in orig_uncov: 
            #
            # match uncovered line regexp
            uncov_match =  uncov_somthing.match(line.rstrip())
            #
            # Write source file name - on first uncovered line of function 
            if filepathe_patt.match(line):
                new_srcfile = True
                src_path = line
            
            
            if uncov_match:
                #
                # Write src file name only after we know it has uncoverd paths
                if new_srcfile:
                    new_srcfile = False
                    if uncov_count > 0:
                        outfp.write('\n\n\n')
                    print(src_path)
                    outfp.write(src_path)
                #
                # Line is uncovered lets find out what type of line it is...

                currcodeline_number = int(uncov_match.group(1))
                uncov_count += 1
                #
                #-->F    283      if (cmd.pbl_size == 0)
                #  -->f 2079c                      !GPRE_FID(vfValid))
                if uncov_condition.match(line):
                    #
                    #get the actual condition
                    condition = uncov_condition.match(line).group(1)
                    if any(not condition in ignor_line.rstrip() for ignor_line in ignor_list):
                        if line.startswith('-->F') or line.startswith('-->T'):
                            outfp.write('\n')
                        outfp.write(line)
                #
                #-->      50                  default:
                elif uncov_defult.match(line):
                    if ignore_default:
                        continue
                    else:
                        outfp.write('\n {}'.format(line))
                #
                #-->      48                  case mEthContextlessSlowpath_EVENTID: // context i
                elif uncov_case.match(line):
                    #
                    #get actual case
                    case = uncov_case.match(line).group(1)
                    if any(not case in ignor_line.rstrip() for ignor_line in ignor_list):
                        #
                        #Keep case from same switch one line after another
                        if currcodeline_number - prevcodeline_number != 1:
                            outfp.write('\n')
                        outfp.write(line)
                #
                #Unreached function condition etc.
                #-->     293      if(tpaAggIndex<32)
                #-->     282  INLINE bool  mEthTpaIfAggIndexAviliable(DECLARE_CPARAMS, uint8 tpaAggIndex)
                else:
                    unreached_line = uncov_match.group(2)
                    if any(not unreached_line in ignor_line.rstrip() for ignor_line in ignor_list):
                        outfp.write('\n{}'.format(line))

                prevcodeline_number = currcodeline_number

    return uncov_count


def tstcov(tst_name, tst_srcpath, ignore_list, ouput_path):
    
    my_output = '{}{}_cov.txt'.format(ouput_path, tst_name)
    be_output = '{}{}_Origcov.txt'.format(ouput_path, tst_name)

    with open(be_output, 'w') as orig_out:
        p = subprocess.Popen('covbr -u -c0 -dDir {}'.format(tst_srcpath), stdout=orig_out, stderr=subprocess.PIPE)
        out, err = p.communicate()
	    #TODO: verify return code

    with open(be_output, 'r') as orig_out:
        amountuncov  = create_clean_covoutput(orig_out, ignore_list, )


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

        all_tests_passed = True
        print('Bullseye Covarege reslut\n')

        for tstname, res in succsess_dict.items():
            all_tests_passed = all_tests_passed and res
            if not res:
                print('test: {} Failed!!!'.format(tstname, res))
            else:
                print('test: {} Passed'.format(tstname, res))


if __name__ == '__main__':
  main()