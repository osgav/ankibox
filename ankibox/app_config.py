#!/usr/bin/env python
#
# ankibox script 2.0
#
# Config module
#
# osgav 2023
#


import logging
import os
import tomli




class ConfigValidator:
    '''
    ensure the folders are folders and the files are files...
    '''
    def __init__(self, config):
        '''
        the point of this class is to alleviate the AnkiNote class
        of having the validate the "path" properties in config.toml
        '''
        self.log = logging.getLogger(self.__class__.__name__)
        self.config = config

    def validate_config(self):
        self.check_folder_paths()
        self.check_file_paths()

    def check_folder_paths(self):
        # TODO: INSERT ERROR HANDLING HERE
        self.log.debug("checking folders...")
        for folder in self.config['folder']:
            # self.log.debug(folder)
            if os.path.isdir(folder['path']):
                pass
            else:
                self.log.debug("path for \"{}\" is not a folder!".format(folder['name']))
                exit()

    def check_file_paths(self):
        # TODO: INSERT ERROR HANDLING HERE
        self.log.debug("checking files...")
        for file in self.config['file']:
            if os.path.isfile(file['path']):
                pass
            else:
                self.log.debug("path for \"{}\" is not a file!".format(file['name']))
                exit()




class Config:
    '''
    thank you to: 
    
    https://charlesreid1.github.io/a-singleton-configuration-class-in-python.html

    for the style of Config object here. i.e.

    - load content of config file into a class variable
    - provide static methods for accessing that class variable

    this allows values in the config file to be accessed
    by any class in the script that imports this Config object
    provided the Config object is instantiated somewhere first

    terrible place for a note:
    - this other post is similar
    - https://www.hackerearth.com/practice/notes/samarthbhargav/a-design-pattern-for-configuration-management-in-python/
    - it uses @property
    '''

    _config = None

    def __init__(self, cli_args):
        self.log = logging.getLogger(self.__class__.__name__)
        self.log.debug("initializing Config object...")
        self.cli = cli_args
        # self.locate_config_file()
        self.load_config_file()
        self.validate_config_file()


    def locate_config_file(self):
        if self.cli.config:
            self.log.debug("config file location specified in command line arguments")
        else:
            self.log.debug("command line arguments did not specify a config file")
        #
        # this function should either:
        #
        # - use the config specified at the command line
        # - use the config specified via an env var
        # - use the config found in the default location
        #
        # it's generally going to use the one in the default location.
        # i don't think i'll even bother adding the env var option...
        # i might not even finish adding the cli arg capability properly?
        # right now, load_config_file() uses a hardcoded location
        # and that's good enough.
        #

    def load_config_file(self):
        CONFIG = "/home/doj/.ankibox/config.toml" # HARDCODED VALUE ...
        # CONFIG = "./ankiboxtestvault-config.toml" # HARDCODED VALUE ...
        with open(CONFIG, "rb") as f:
            Config._config = tomli.load(f)

    def validate_config_file(self):
        cv = ConfigValidator(Config._config)
        cv.validate_config()

    # @staticmethod
    # def get_folders():
    #     return Config._config['folder']

    # @staticmethod
    # def get_files():
    #     return Config._config['file']

    @staticmethod
    def get_config_item(item):
        return Config._config[item]
