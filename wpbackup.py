import sys
import os
import re
import subprocess
import shutil
import tarfile
import datetime


try:
    import pysftp
except:
    print()
    print("pytsftp , module Not Found")
    print("Install: pip3 install pysftp")
    sys.exit(1)

########################################    
# Remote sftp server Connection Details.
########################################

SFTP_HOST = '192.168.1.5'       
SFTP_USER = 'backupuser'
SFTP_PASSWD = 'clado123'
SFTP_DIR = '/home/backupuser/'
SFTP_PORT = '22'


##############################################################
# Temp location to store local sql.dump and wrodpress archive.
##############################################################

BACKUP_DIRECTORY = '/tmp/wpbackup'




def parsing_wpconfig(install_location): 
    """
    - This function takes wordpress installation directory as argument.
    - Parse wp-config.php and retrive all database information for backup.
    - return {'database':database,'user':user, 'password':password, 'host':host}     
    """
    try:
        print('{:<5}{:30}{:^2}'.format('LOG: ','Parsing wp-config.php File',':'),end='')
        config_path = os.path.normpath(install_location+'/wp-config.php') 
        with open(config_path) as fh:
                content = fh.read()
        regex_db = r'define\(\s*?\'DB_NAME\'\s*?,\s*?\'(?P<DB>.*?)\'\s*?\);'
        regex_user = r'define\(\s*?\'DB_USER\'\s*?,\s*?\'(?P<USER>.*?)\'\s*?\);'
        regex_pass = r'define\(\s*?\'DB_PASSWORD\'\s*?,\s*?\'(?P<PASSWORD>.*?)\'\s*?\);'
        regex_host = r'define\(\s*?\'DB_HOST\'\s*?,\s*?\'(?P<HOST>.*?)\'\s*?\);'         
        databse = re.search(regex_db,content).group('DB')
        user = re.search(regex_user,content).group('USER')
        password = re.search(regex_pass,content).group('PASSWORD')
        host = re.search(regex_host,content).group('HOST')
        print('Completed')
        return {'database':databse, 
                'user':user, 
                'password':password, 
                'host':host
                }  
    
    except FileNotFoundError:
        print('Falied')
        print('File Not Found,',config_path)
        sys.exit(1) 
        
    except PermissionError:
        print('Falied')
        print('Unable To read Permission Denied,',config_path)
        sys.exit(1)
        
    except AttributeError:
        print('Falied')
        print('Parsing Error wp-config.php seems to be corrupt,')
        sys.exit(1)

        
        
def take_sqldump(db_details):
    """
    - This function takes parsing_wpconfig as argument.
    - Create database backup using db_details dictionary.
    """    
    print('{:<5}{:30}{:^2}'.format('LOG: ','Creating DataBase Dump',':'),end='')

    try:
        USER = db_details['user']
        PASSWORD = db_details['password']
        HOST = db_details['host']
        DATABASE = db_details['database']
        DUMPNAME = os.path.normpath(os.path.join(BACKUP_DIRECTORY,db_details['database']+'.sql')) 
        cmd = "mysqldump  -u {} -p{} -h {} {}  > {} 2> /dev/null".format(\
                                    USER, PASSWORD, HOST, DATABASE, DUMPNAME)
        subprocess.check_output(cmd,shell=True) 
        print('Completed')
        return DUMPNAME
    
    except subprocess.CalledProcessError:
        print('Failed')
        print(': MysqlDump Failed.')
        sys.exit(1)
        
    except: 
        print('Failed')
        print(': Unknown Error Occurred.')
        sys.exit(1)    
        


def make_archive(wordpress_path,dumpfile_path):  
    """
    - This function takes wordpress install path & sqlfile dump path as args.
    - create an gzip arive under BACKUP_DIRECTORY.
    """
    try:
        print('{:<5}{:30}{:^2}'.format('LOG: ','Archiving WordPress & SqlDump',':'),end='')

        time_tag = datetime.datetime.now().strftime('%Y-%m-%d-%H-%M-%S')
        dir_name = os.path.basename(wordpress_path.rstrip('/'))
        archive_name = os.path.normpath(BACKUP_DIRECTORY+'/'+dir_name+'-'+time_tag+'.tar.gz')
        
        with tarfile.open(archive_name, "w:gz") as tar:
            tar.add(wordpress_path)
            tar.add(dumpfile_path,arcname="sql.dump")
        print('Completed')   
        return archive_name

    except FileNotFoundError:
        print('Falied')
        print(': File Not Found,',tar_name)
        sys.exit(1) 
        
    except PermissionError:
        print('Falied')
        print(': PermissionError Denied While Copying.')
        sys.exit(1)
        
    except:
        print(': Unknown error occurred while taring directory :',location)
        sys.exit(1)
        

    
def sftp_upload(archive_path):
    """
    - Upload archive to sftp server.
    """
    print('{:<5}{:30}{:^2}'.format('LOG: ','Uploading Files To SFTP',':'),end='')
    try:
        cnopts = pysftp.CnOpts()
        cnopts.hostkeys = None 
        with pysftp.Connection(SFTP_HOST,username=SFTP_USER,password=SFTP_PASSWD,port=int(SFTP_PORT),cnopts=cnopts) as sftp:
            if not sftp.exists(SFTP_DIR):
                sftp.makedirs(SFTP_DIR)
            sftp.cwd(SFTP_DIR)
            sftp.put(archive_path)
            sftp.close()
        print('Completed')
        
    except AuthenticationException:
        print('Failed')
        print(': Sftp Authentication Failure.')
        sys.exit(1)
        
    except PermissionError:    
        print('Failed')
        print(': Permission Denied Error From Server.')
        sys.exit(1)
    except:
        print('Failed')
        print(': Unknown Error Occurred.')
        sys.exit(1)    

        
def remove_backupdir():
    """
    - Creating BACKUP_DIRECTORY which holds sql sump and archive files.
    """
    if os.path.exists(BACKUP_DIRECTORY):
        shutil.rmtree(BACKUP_DIRECTORY)       

        
def make_backupdir(location):
    """
    - remove BACKUP_DIRECTORY which holds sql sump and archive files.
    """
    if not os.path.exists(location):
        os.makedirs(location)

        
def main():
    arguments = sys.argv[1:]
    if arguments:
        for location in arguments:
            install_dir = location
            if os.path.exists(install_dir):
                print('')
                print('Backup Process of :',install_dir)
                make_backupdir(BACKUP_DIRECTORY)
                database_info = parsing_wpconfig(install_dir)
                dump_location = take_sqldump(database_info)
                archive_path = make_archive(install_dir,dump_location)
                sftp_upload(archive_path)

            else:
                print('')
                print('Error: Path Not Found',install_dir)
                print('')

            remove_backupdir()
    else:
        print('')
        print("Description: Python script to backup wordpress website into remote server.")
        print('')
        print("This Script will backup wordpress and database information")
        print("and upload them into a remote sftp server.")
        print('')
        print('USAGE: ./wpbackup.py install_path')
        print('')
        
if __name__ == '__main__':
    main()
