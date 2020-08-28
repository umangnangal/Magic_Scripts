#!/usr/bin/python
""""
Author:
    Umang Agrawal (umagrawa@cisco.com)
Description:
    Generates a compilation warning analysis report for user specified modules or \
    for all the modules using the logfiles already present in the build directory.
"""
#Importing Required Packages
import os,shutil,glob,io,time,re
from collections import defaultdict
import sys

def warning_analyze_print(name = ''):
    print('Analyzing the warnings for {0}'.format(name))
    total_warnings = 0 
    final_report = []
    for file in glob.glob('*'):
        #Getting labels for classifying the warnings
        div_set = set()
        div_set.add('-Others')
        f = io.open(file, 'r', encoding='latin1')
        for line in f:
            line = line.strip()
            if 'warning' in line and '.mk' not in line and '.c' in line and '.cli' not in line:
                match = re.findall(r"\[\D*\]", line)
                if(match):
                    div_set.add(match[0])

        #Creating a dictionary for maintaing count for each warning type
        warning_count = {}
        for item in div_set:
            warning_count[item] = 0

        others = []
        f = io.open(file, 'r', encoding='latin1')
        count = 0
        for line in f:
            line = line.strip()
            if 'warning' in line and '.mk' not in line and '.c' in line and '.cli' not in line and '.cmd' not in line:
                flag=0
                for i in warning_count.keys():
                    if i in line:
                        warning_count[i] = warning_count[i] + 1 
                        count += 1
                        flag = 1
                        break
                if (flag==0):
                    others.append(line)
                    count += 1
                    warning_count['-Others'] = warning_count['-Others'] + 1 
        f.close()
        
        #Checking the build result ie. DONE or FAILED
        f = io.open(file, 'r', encoding='latin1')
        ret_val = 'Unexpected Error. Please check the log.'
        data = f.readlines()
        try:
            if 'FAILED' in data[-4]:
                ret_val = 'BUILD FAILED'
            elif 'DONE' in data[-2]:
                ret_val = 'DONE'
        except IndexError:
            print('Not enough log generated. Please check the log.')

        final_report.append((file, count, ret_val))

        #Prints detailed analysis of the warnings
        print('\n*********' + file + '*********')
        warning_count_list = []
        for div, div_count in warning_count.items():
            if div_count>0:
                warning_count_list.append((div, div_count))
        
        warning_count_list.sort(key = lambda x:x[1], reverse = True)
        for item in warning_count_list:
            print( item[0] + '-'*(50-len(item[0])) + str(item[1]) )
        if len(others)>0:
            print('!!!Unclassified warnings are given below:')
            for i in range(len(others)):
                print(str(i+1)+') ' + others[i])

    print('\n'+'*'*100)
    final_report.sort(key = lambda x:x[1], reverse = True)
    print("FINAL REPORT FOR COMPILATION WARNINGS :\n")
    for i in range(len(final_report)):
        print(str(i+1)+ ') ' + final_report[i][0] + ' ' + '-'*(60-len(final_report[i][0])-len(str(i+1))) + ' ' + str(final_report[i][1]) + '\t' + final_report[i][2] )
        total_warnings += final_report[i][1]
    print('\nTOTAL WARNINGS TO BE RESOLVED for {0} : {1}\n'.format(name, total_warnings))

def ccw_report():
    module_list = []
    log_files = []
    
    #Parsing Arguments
    if len(sys.argv) == 1:
        print('!!! Please refer to help. Use -h or -help after the cli ')
        raise ValueError('Positional Argument not present')
    elif  len(sys.argv) == 2 and sys.argv[1] in ['-h', '-help'] :
        print('''\nUse one of the following 2 arguments to build the specified modules and analyze the compilation warnings.
                -module < >            :    Provide comma separated module names.
                -module_filelist < >   :    Provide the name of the file consisting of the module names each in a new line.
                 Eg. ./ccw_report -module ddas,rscn,fspf 
                     ./ccw_report -module_filelist file.txt\n''')

        print('''Use one of the following 3 arguments to analyze compilation warnings in the existing logfiles present in the build directory.
                -all                     :    Analyze all the build logfiles present in the build directory.
                -buildlog < >            :    Provide comma separated build logfile names.
                -buildlog_filelist < >   :    Provide the name of the file consisting of the build logfile names each in a new line.
                 Eg. ./ccw_report -all 
                     ./ccw_report -buildlog log.images^final^fcoe_n9000,log.images^final^eth_n9000
                     ./ccw_report -buildlog_filelist file.txt ''')

    elif len(sys.argv) == 3 and sys.argv[1] in ['-module', '-module_filelist'] :
        input_type = sys.argv[1]
        if input_type == '-module_filelist' :
            module_file = sys.argv[2]
            try:
                file = open(module_file, 'r')
            except:
                print("File '{0}' does not exist. Please create '{1}' and write every module to be analyzed in new line.".format(module_file, module_file))
                raise IOError
            else:
                module_list = [line.strip() for line in file if line.strip()]
            finally:
                file.close()
        elif input_type == '-module' :
            module_list = [x.strip() for x in sys.argv[2].split(',')]
        else :
            print('Wrong Arguments')
            raise ValueError('See help')
        
        dirName = 'compilation_warnings'
        os.chdir('./..')
        print('Directory changed to {0}'.format(os.getcwd()))
        #Creating a directory for storing the build logs for each module
        if not os.path.exists(dirName):
            os.mkdir(dirName)
            print("Directory " + dirName + " created ")
        else:    
            print("Directory " + dirName + " already exists. Deleting the existing directory...")
            shutil.rmtree(dirName)
            os.mkdir(dirName)
            print("Directory " + dirName + " created ")

        #Getting into the build directory
        os.chdir('./build')
        print('Directory changed to {0}'.format(os.getcwd()))
        print('*** Make sure to run required vbe 5.x.x.x before using gmake ***')
        print('\nExecuting build for following modules:')
        for module in module_list:
            print(module)

        #Executing the build commands to generate the compilation warnings log
        for module in module_list:
            print('\nGetting the build targets for module : {0}'.format(module))
            cmd_get_targets = './InsBuild -module {0} -bldtype final -image nxos -show_only > tmp.txt 2>&1 < /dev/null'.format(module)
            print('Executing cli : {0}'.format(cmd_get_targets))
            os.system(cmd_get_targets)
            targets = []
            var = 0 ; bracket = 0
            f = io.open('tmp.txt', 'r', encoding='latin1')
            for line in f:
                if '$VAR1' in line:
                    var = 1
                elif var == 1 and bracket == 0 and ']' not in line:
                    targets.append( ''.join(x for x in list(line.strip()) if x not in [',', "'"]) )
                elif var == 1 and ']' in line:
                    bracket = 1
                    break
            f.close()
            if len(targets):
                print('Targets found for {0}:'.format(module))
                for target in targets:
                    print(target)
            else:
                print('No targets found for {0}. Please check the module name.'.format(module))
            
            print('\n*** Cleaning all the targets... ***')
            for target in targets:
                cmd_clean = 'gmake clean {0} &> /dev/null'.format(target)
                print('Executing cli : {0}'.format(cmd_clean))
                os.system(cmd_clean)

            print('\n*** Building all the targets... ***')
            start = time.time()
            print('Starting build for module : {0}'.format(module))
            cmd_insbuild = './InsBuild -module {0} -bldtype final -image nxos > ./../{1}/{2} 2>&1 < /dev/null'.format(module, dirName, module)
            print('Executing cli : {0}\nIt will take around 30 minutes, please wait.....'.format(cmd_insbuild))
            os.system(cmd_insbuild)
            end = time.time()
            print('TIme Elapsed : {0} minutes\n'.format( (end-start)//60 ) )
            
        #Warning Analysis Report Generation

        os.chdir('./../' + dirName)
        print('Directory changed to {0}'.format(os.getcwd()))
        print('\n' + '*'*20 + 'COMPILATION WARNING ANALYSIS' + '*'*20 +' \n')
        warning_analyze_print('selected modules')
        os.chdir('./..')

    elif len(sys.argv) >=2 and sys.argv[1] in ['-buildlog', '-buildlog_filelist', '-all'] :
        input_type = sys.argv[1]
        if input_type == '-all' :
            for file in glob.glob('*'):
                if 'log.images^final^' in file and '.cli' not in file:
                    log_files.append(file)
        elif input_type == '-buildlog_filelist' :
            logfile = sys.argv[2]
            try:
                file = open(logfile, 'r')
            except:
                print("File '{0}' does not exist. Please create '{1}' and write every logfile to be analyzed in new line.".format(logfile, logfile))
                raise IOError
            else:
                log_files = [line.strip() for line in file if line.strip()]
            finally:
                file.close()
        elif input_type == '-buildlog' :
            log_files = [x.strip() for x in sys.argv[2].split(',')]
        else :
            print('Wrong Arguments')
            raise ValueError('See help')

        module_path_file = './defs/modulepath.mk'
        module_path2name = {}

        f = io.open(module_path_file, 'r', encoding='latin1')
        for line in f:
            if ':=' in line:
                line = line.strip().partition(':=')
                module_path2name[line[2].strip()] = line[0].strip().rpartition('_')[0]
            elif '=' in line:
                line = line.strip().partition('=')
                module_path2name[line[2].strip()] = line[0].strip().rpartition('_')[0]
        f.close()

        os.chdir('./..')
        dirName = 'baseline_warnings'
        #Creating a directory for storing the build logs for each module
        if not os.path.exists(dirName):
            os.mkdir(dirName)
            print("Directory " + dirName + " created ")
        else:    
            print("Directory " + dirName + " already exists. Deleting the existing directory...")
            shutil.rmtree(dirName)
            os.mkdir(dirName)
            print("Directory " + dirName + " created ")


        for log_file in log_files:
            os.chdir('./build')
            warning_record = defaultdict(list)
            others = []
            f = io.open(log_file, 'r', encoding='latin1')
            for line in f:
                line = line.strip()
                if 'warning' in line and '.mk' not in line and '.c' in line and '.cli' not in line:
                    line = line.replace('//', '/')
                    warning = line
                    line = [ x for x in line.partition(':')[0].split('/') if '.c' not in x]
                    loop = len(line)
                    flag = 0
                    while(loop>0):
                        path = '/'.join(line[:loop]).strip()
                        if path in module_path2name.keys():
                            warning_record[module_path2name[path]].append(warning)
                            flag = 1
                            break
                        else:
                            loop -= 1
                    if flag == 0 :
                        others.append(warning)
            f.close()

            #Entering baseline_warnings Directory
            os.chdir('./../' + dirName)
            os.mkdir(log_file)
            os.chdir('./' + log_file)
            for key in warning_record.keys():
                with open(key, 'w') as file:
                    for item in warning_record[key]:
                        file.write(item + '\n')
            if len(others)>0:
                with open('others', 'w') as file:
                    for item in others:
                        file.write(item + '\n')
            os.chdir('./../..')

        os.chdir('./' + dirName)
        for directory in glob.glob('*'):
            os.chdir('./' + directory)
            warning_analyze_print(directory)
            os.chdir('./..')
    else:
        print('Wrong Arguments. Please see help.')
        raise ValueError("Please refer the help using './ccw_report -help' " )
 

if __name__ == "__main__":
    ccw_report()
    print('\nFor more info, please refer : https://wiki.cisco.com/display/DC3SW/Compilation+Warning+Analyser ')