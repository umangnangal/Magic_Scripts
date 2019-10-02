#!/usr/bin/python
""""
Author:
    Umang Agrawal (umagrawa@cisco.com)
Description:
    Generates a SA warning analysis report by running the static_docs script for multiple components in one go.
"""
#Importing Required Packages
import os,shutil,glob,io,time
from collections import defaultdict
import sys

def sa_log_generation():
    module_list = []
    #Parsing Arguments
    if len(sys.argv) == 1:
        print('!!! Please refer to help. Use -h or -help.')
        print('''
        Correct usage:  ./saw_report_v3 -comp_filelist <comp_list> -branch <branch_name> 
                        ./saw_report_v3 -comp <comp_name> -branch <branch_name> 
        NOTE : Component name should be relative to the root directory of the pulled LBT
        ''')
        raise ValueError('Positional Argument not present')
    elif  len(sys.argv) == 2 and sys.argv[1] in ['-h', '-help'] :
        print('''
        Use one of the following 2 arguments to build the specified components and analyze the SA warnings.
                -comp < >            :    Provide comma separated component names.
                -comp_filelist < >   :    Provide the name of the file consisting of the component names each in a new line.

        Eg. ./saw_report_v3 -comp infra/port_manager/fc-pm -branch iplus_dev
            ./saw_report_v3 -comp infra/port_manager/fc-pm -branch davis
            ./saw_report_v3 -comp_filelist file.txt -branch skywalker 
            ''')

    elif len(sys.argv) == 5 and sys.argv[1] in ['-comp', 'acme_comp', '-comp_filelist'] :
        input_type = sys.argv[1]
        if input_type == '-comp_filelist' :
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
        elif input_type == '-comp' :
            module_list = [x.strip() for x in sys.argv[2].split(',')]
        else :
            print('Wrong Arguments')
            raise ValueError('See help')

        count_dir = 'sa_warning_count'
        os.chdir('./..')
        print('Directory changed to {0}'.format(os.getcwd()))
        #Creating a directory for storing the build logs for each component
        if not os.path.exists(count_dir):
            os.mkdir(count_dir)
            print("Directory " + count_dir + " created ")
        else:    
            print("Directory " + count_dir + " already exists. Deleting the existing directory...")
            shutil.rmtree(count_dir)
            os.mkdir(count_dir)
            print("Directory " + count_dir + " created ")

        #Getting the lineup of components from .ACMEROOT/ws.lu of ROOT, N7KMDS, COMMON
        print('Getting the lineup of components from .ACMEROOT/ws.lu of ROOT, N7KMDS, COMMON .......')
        ROOT_lineup = []
        N7KMDS_lineup = []
        COMMON_lineup = []

        print('Getting list of components in ROOT.....')
        f = io.open('.ACMEROOT/ws.lu', 'r', encoding='windows-1252')
        for line in f:
            ROOT_lineup.append( line.split(' ')[0] )

        print('Getting list of components in N7KMDS sub_ws.....')
        try:
            f = io.open('./N7KMDS/.ACMEROOT/ws.lu', 'r', encoding='windows-1252')
        except IOError:
            print('*File not present. It may be an N9K workspace*')
        else:
            for line in f:
                N7KMDS_lineup.append( line.split(' ')[0] )
        finally:
            f.close()

        print('Getting list of components in COMMON sub_ws.....')
        try:
            f = io.open('./COMMON/.ACMEROOT/ws.lu', 'r', encoding='windows-1252')
        except IOError:
            print('*File not present. It may be an N9K workspace*')
        else:
            for line in f:
                COMMON_lineup.append( line.split(' ')[0] )
        finally:
            f.close()

        module_list_check = []
        print('\nPerforming SA Warning Analysis for following components:')
        for module in module_list:
            found = ''
            module_new = ''
            if module in COMMON_lineup:
                module_new = 'COMMON/' + module
                found = 'changed to '
            elif module in N7KMDS_lineup:
                module_new = 'N7KMDS/' + module
                found = 'changed to '
            elif module in ROOT_lineup:
                found = 'no change required'
                module_new = module
            else:
                found = 'no change required'
                module_new = module

            module_list_check.append(module_new)
            print(module + ' ----- ' + found + ' ----- ' + module_new)
        
        print('\nTime for a COFFEE BREAK !!!')

        #Creating a directory for storing the log vgenerated by coverity for each component
        log_dir = 'sa_warning_logs'
        if not os.path.exists(log_dir):
            os.mkdir(log_dir)
            print("\nDirectory " + log_dir + " created ")
        else:    
            print("\nDirectory " + log_dir + " already exists. Deleting the existing directory...")
            shutil.rmtree(log_dir)
            os.mkdir(log_dir)
            print("Directory " + log_dir + " created ")

        for module in module_list_check:
            print('\nStarting SA Warning Analysis and saving the log for component: {0}'.format(module))
            if len(sys.argv)>=3 :
                branch = sys.argv[4]
                cmd1 = '/auto/andatc/independent/acme_scripts/1.0/bin/static_dcos -acme_comp {0} -branch {3} > ./{1}/{2} 2>&1 < /dev/null'.format(module, count_dir, module.replace('/','.'), branch)
            
            start = time.time()
            print('Executing cli : {0}\nIt will take around 10 minutes, please wait.....'.format(cmd1))
            os.system(cmd1)
            log_copy_cmd = 'cp ./build/ses_static_analysis.log ./{0}'.format(log_dir)
            log_rename_cmd = 'mv ses_static_analysis.log {0}'.format(module.replace('/','.'))
            print('Executing {0} '.format(log_copy_cmd))
            os.system(log_copy_cmd)
            os.chdir('./{0}'.format(log_dir))
            print('Executing {0} '.format(log_rename_cmd))
            os.system(log_rename_cmd)
            os.chdir('./..')
            print('SA Warning Count generated and saved at {0}/{1}/{2}'.format(os.getcwd(), count_dir, module.replace('/','.')))
            print('SA Warning Detailed Log for component {0} generated and saved at {0}/{1}/{2}'.format(os.getcwd(), log_dir, module.replace('/','.')))
            end = time.time()
            print('TIme Elapsed : {0} minutes\n'.format( (end-start)//60 ) )
        
        data = []
        os.chdir('./{0}'.format(count_dir))
        print('Directory changed to {0}'.format(os.getcwd()))
        for file in glob.glob('*'):
            error= True
            f = io.open(file, 'r', encoding='windows-1252')
            flag = -1
            for line in f:
                if 'warnings:' in line and flag == -1:
                    flag = 0
                    error = False
                    active = int(line.partition(':')[2].strip())
                elif 'warnings:' in line and flag == 0:
                    flag = 1
                    noise= int(line.partition(':')[2].strip())
                elif 'warnings:' in line and flag == 1:
                    flag = 2
                    parent = int(line.partition(':')[2].strip())
                elif 'Static analysis warnings can be viewed at' in line:
                    coverity_link = line.partition(':')[2]
                
            if error:
                data.append((file.replace('.','/'), 'Coverity not working', ' ', ' ', 'link not found'))
            else:
                data.append((file.replace('.','/'), active, noise, parent, coverity_link))
            f.close()

        print('********** SA Warnings Analysis Report **********')
        print('Module' + ' '*(50-len('Module')) + '  ' + 'Active' + '  ' +  'Noise' + '  ' +  'Parent' )
        for i in data:
            print(i[0] + '-'*(50-len(i[0])) + '     ' + str(i[1]) + '     ' +  str(i[2]) + '     ' + str(i[3]) )
        for i in data:
            print('\nStatic analysis warnings coverity web-link for {0} can be viewed at :\n {1}\n'.format(i[0], i[4]))

    else:
        print('!!! Please refer to help. Use -h or -help.')
        print('''
        Correct usage:  ./saw_report_v3 -comp_filelist <comp_list> -branch <branch_name> 
                        ./saw_report_v3 -comp <comp_name> -branch <branch_name> 
        NOTE : Component name should be relative to the root directory of the pulled LBT
        ''')
        raise ValueError('Positional Argument not present')

    os.chdir('./..')

def sa_warning_analysis(file):
    warning_record = dict()
    with open(file) as f:
        line = f.readline().strip()
        while (True):
            if '@@' in line :
                file_name = "/".join(line.rsplit("/", 4)[1:])
                count = 0
                if file_name not in warning_record.keys():
                    warning_record[file_name] = defaultdict(list) 
                line = f.readline().strip()
                
            elif '**' in line and count == 0:
                while(True):
                    line = f.readline().strip()
                    if '**' in line:
                        count = 1
                        break
                    elif '**' not in line:
                        if (':' in line):
                            try:
                                filename, lin_no, sev, div, warning = line.split(':',4)
                                warning_record[file_name]['Active'].append((filename, lin_no, sev, div, warning))
                            except ValueError:
                                print(line.split(':'))
                        
            elif '**' in line and count == 1:
                while(True):
                    line = f.readline().strip()
                    if '**' in line:
                        count = 2
                        break
                    elif '**' not in line:
                        if (':' in line):
                            try:
                                filename, lin_no, sev, div, warning = line.split(':',4)
                                warning_record[file_name]['Noise'].append((filename, lin_no, sev, div, warning))
                            except ValueError:
                                print(line.split(':'))

                        
            elif '**' in line and count == 2:
                while(True):
                    line = f.readline().strip()
                    if '**' in line:
                        count = 3
                        break
                    elif '@@' in line :
                        break
                    elif line == '' :
                        break
                    elif '**' not in line:
                        if (':' in line):
                            try:
                                filename, lin_no, sev, div, warning = line.split(':',4)
                                warning_record[file_name]['Parent'].append((filename, lin_no, sev, div, warning))
                            except ValueError:
                                print(line.split(':'))

            
            elif 'Total' in line :
                break
            
            else:
                line = f.readline().strip()

    #Getting the labels for classification of SA Warnings
    div_set = set()
    for key in warning_record.keys():
        for warning_list in warning_record[key].values():
            for item in warning_list:
                div_set.add(item[3])

    #Creating a dictionary for maintaing count for each warning type
    div_type_count = {}
    for item in div_set:
        div_type_count[item] = 0

    #Iterating through the warnings to get the count of eah warning type
    for key in warning_record.keys():
        for warning_list in warning_record[key].values():
            for item in warning_list:
                div_type_count[item[3]] = div_type_count[item[3]] + 1

    final_report = []   
    for div, div_count in div_type_count.items():
        if div_count > 0:
            final_report.append((div, div_count))
    print('\n********** ' + file + ' **********')
    final_report.sort(key = lambda x:x[1], reverse = True)
    for item in final_report:
        print( item[0] + '-'*(50-len(item[0])) + ' ' + str(item[1]) )
    print('\n')

    
    #File-based report generation
    print('\nFile-based warning count\n')
    file_based_count = []
    for key in warning_record.keys():
        data = warning_record[key]
        count = len(data['Parent']) + len(data['Noise']) + len(data['Active'])
        file_based_count.append((key, count))

    file_based_count.sort(key = lambda x:x[1], reverse = True)
    for item in file_based_count:
        print( item[0] + '-'*(50 - len(item[0])) + str(item[1]) ) 


    """
    #Current Requirement.....removing warnings for RESOURCE_LEAK and NEGATIVE_RETURNS
    print("Choose from the given warning types : ")
    print(div_set)
    if len(sys.argv) == 6 and sys.argv[5] == '-noprompt':
        category = list(div_set)
    elif len(sys.argv) == 8 and sys.argv[7] == '-noprompt':
        category = list(div_set)
    else:
        category = raw_input("Enter the category of the warnings to be printed (comma separated) : ")
        category = [x for x in category.split(',')]

    print('\nCurrent Requirement.....printing warnings for user-defined categories\n')
    report = []
    other_active = []
    for key in warning_record.keys():
        data = warning_record[key]
        if len(data['Active']) >0 or len(data['Noise']) >0 or len(data['Parent']) >0:
            print('\n' + key)
        count = 0

        if ( len(data['Active']) >0 ):
            print("***** ACTIVE WARNINGS *****")
        for item in data['Active']:
            if item[3] in category:
                count = count + 1
                print('Line : {0} Category : {1} Warning : {2}'.format(item[1], item[3], item[4]))
            else :
                other_active.append(item)

        if ( len(data['Noise']) >0 ):
            print("***** NOISE WARNINGS *****")
        for item in data['Noise']:
            if item[3] in category:
                count = count + 1
                print('Line : {0} Category : {1} Warning : {2}'.format(item[1], item[3], item[4]))

        if ( len(data['Parent']) >0 ):
            print("***** PARENT WARNINGS *****")        
        for item in data['Parent']:
            if item[3] in category:
                count = count + 1
                print('Line : {0} Category : {1} Warning : {2}'.format(item[1], item[3], item[4]))

        if(count > 0):
            report.append( (key, count) )
        
    report.sort(key = lambda x:x[1], reverse = True)
    if len(report)> 0:
        print('\n********** File-based distribution  **********\n')
        for item in report:
            print( item[0] + '-'*(70 - len(item[0])) + str(item[1]) )
    
    if(len(other_active) > 0 ):
        print( '\n!!! Other active warnings to be resolved to commit !!!    COUNT : {0}'.format(len(other_active)) )
        for item in other_active:
            print('File : {0} Line : {1} Category : {2} Warning : {3}'.format(item[0],item[1], item[3], item[4]))
"""

if __name__ == "__main__":
    sa_log_generation()
    if len(sys.argv) >= 3 and sys.argv[1] in ['-comp', '-comp_filelist'] :
        os.chdir('./sa_warning_logs')
        for file in glob.glob('*'):
            sa_warning_analysis(file)
        
        print('Current directory is ' + os.getcwd())
        try:
            copy_cmd1 = 'cp /ws/umagrawa-sjc/analyzer1 .'
            copy_cmd2 = 'cp /ws/umagrawa-sjc/analyzer2 .'
            print('Executing cli ' + copy_cmd1)
            os.system(copy_cmd1)
            print('Executing cli ' + copy_cmd2)
            os.system(copy_cmd2)
            print('analyzer1 and analyzer2 scripts are copied to sa_warning_logs directory.')
        except FileNotFoundError:
            print('Error while copying file from /ws/umagrawa-sjc. Please check if file is present in that workspace.')
        
        print(''' 
'sa_warning_count' and 'sa_warning_logs' directories are generated in the root directory. 
If you want the data in a more organised manner(in a .csv format), please copy the sa_warning_logs to your local machine(with python v3.x with pandas installed) and run 'analyzer1' and 'analyzer2' python scripts.
They will generate 'report1.csv'and 'report2.csv' in the same directory.''')

    print('\nFor more info, please refer : https://wiki.cisco.com/display/DC3SW/SA+Warning+Analyser ')