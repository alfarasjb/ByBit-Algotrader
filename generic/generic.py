"""
This file contains generic methods that are used for interacting with user actions. Loading selected strategies, 
configurations, etc. 
"""

import importlib.util
import sys
import os
from typing import List, Any, Optional, Dict, Union


def is_blank(value: str) -> bool:
    """
    Receives a string input and determines whether input is blank/whitespace
    
    Parameters
    ----------
        value: str
            Input value to check if blank/whitespace
    """

    # Determines if value is blank
    if len(value.strip()) == 0:
        return True 
    
    # Determines if value is whitespace
    return value.isspace() 


def validate_integer_input(value: str, min_value: int = None) -> bool:
    """
    Receives user input as string, and validates if received input is an integer. 

    Called by get_integer_value()

    Values that are considered valid:
    1. Integer value greater than min_value 
    2. Empty Strings - Returns True, use default 
    3. White Spaces - Returns True, use default
    
    Parameters
    ----------
        value: str 
            String value to validate
        
        min_value:int=None
            Minimum value required. Returns Invalid if input value is less than minimum value.
    """
    
    # Returns true if input string is empty. Default will be used
    if len(value) == 0:
        return True 
    
    # Returns true if input is whitespace. Default will be used
    if value.isspace():
        return True

    # Checks if `value` is an integer, and throws and error if casting fails.
    try:
        int(value)
    except ValueError as e:
        print(e)
        return False 
    
    # Checks if value is greater than minimum, only if minimum value is specified 
    assert int(value) > min_value, f"Value must be greater than {min_value}"
    
    # Returns true if no other errors are raised 
    return True 


def generate_options(options: List[Any], show_exit: bool = True) -> None:
    """
    Receives a list of options, and displays an enumeration of the options on the terminal.
    
    Parameters
    ----------
        options: List[Any]
            List of options to print on the terminal 
        
        show_exit:bool
            Prints an Exit options if set to True, allowing the user to exit the current function. 
    """
    if show_exit:
        print("0. Exit")

    for index, option in enumerate(options):
        print(f"{index+1}. {option}")


def error_msg(source: str, value: Any) -> None:
    """ 
    Prints an error message if any inputs hold the incorrect/invalid value.

    Parameters
    ----------
        source: str 
            Name/Title of the desired input 
        
        value: any
            Received value of the input
    """
    print(f"Invalid {source}. Value: {value}")


def prompt(source: str, default: int, min_value: int = None) -> str:
    """
    Returns a string for input prompt. 

    Parameters
    ----------
        source: str 
            Name/Title of the desired input 
        
        default: int 
            Default integer value/index of the input 

        min_value: int 
            Minimum value of the input 
    """
    if min_value is None: 
        return f"\n{source} [{default}]: "
    
    return f"\n{source} [>{min_value}, {default}]: "


def get_integer_value(source: str, default: int, min_value: int = None) -> int:
    """
    Tries to get an integer value as user input. Uses validate_integer_input() to check if input is a valid integer. 
    This is used to get integer values. 

    Parameters
    ----------
        source: str 
            Name/Title of the desired input 
        
        default: int 
            Default integer value of the input 
        
        min_value:int=None
            Minimum value of the input 
    """

    while True:
        # Receives string input 
        val = input(prompt(source, default))
        try:
            # Validates string input as integer 
            valid = validate_integer_input(val, min_value)
            if not valid:
                # Throws error message if input is not integer
                error_msg(source, val)
                # Continues the loop until valid value is received
                continue 
            if is_blank(val):
                # Uses default value if received input is blank/whitespace
                print(f"Using default value for {source}: {default}")
                return default 
            # Returns the input value as an integer if received input is a valid integer, and is not blank. 
            return int(val)
        
        except AssertionError as e:
            # AssertionError is raised if input value is less than minimum value 
            print(f"Error: {e}")


def get_string_value(
        source: str,
        default: int,
        valid_values: List[Any] = None,
        show_exit: bool = False,
        use_str_input: bool = False) -> Optional[str]:
    """ 
    Given a list of options, returns a string value from user input depending on input type: str or int. User may input
    index, or string value.

    Parameters
    ----------
        source: str 
            Name/title of desired input 

        default: int   
            Default integer/index value from options 
        
        valid_values: List[Any]
            List of valid values as user options 
        
        show_exit: bool
            Shows exit option 
        
        use_str_input: bool 
            Receive the input as string instead of index 
    """

    print()
    index_message = f"Use index to select {source}" if not use_str_input else ""
    print(f"{source}: {index_message}")
    # Prints options on terminal 
    generate_options(valid_values, show_exit=show_exit)

    while True:
        # Receives a string value 
        val = input(prompt(source, default))
        try: 
            # Select option using index by default
            val = int(val)
        except ValueError:
            # Throws value error if casting failed, input is not an integer. 
            
            if is_blank(val):
                # Returns default if input is blank/whitespace
                print(f"Using default for {source}: {default}")
                return valid_values[default-1]
            
            if not use_str_input:
                # Continues the loop if string input is received, but use_str_input is disabled for selecting options 
                print("Invalid input. Use index to select file.")
                continue 
            
            # Validates string input if `use_str_input` is enabled
            val_str = val.strip().lower()
            if val_str not in valid_values:
                # Continues the loop if string input is not found in valid values. 
                print(f"Invalid string input for {source}. Value: {val_str}")
                continue 
            
            # Returns string value if string is found in valid_values 
            return val_str 
        
        # Returns None if input is 0 
        if val == 0: 
            print(f"Invalid selected value. Try Again.")
            return None 
        
        try:
            # Returns string value of selected option 
            return valid_values[val-1]
        except IndexError:
            # Raises index error if specified index exceeds available options
            print(f"Invalid selected value. Try Again.")
            continue 


def cfg_as_dict(path: Union[str, Any]) -> Dict:
    """
    Receives a path for config file (.ini) and returns the config as dictionary. 

    Parameters
    ----------
        path:str 
            Path to .ini file. 
            Example: strategies/strategies.ini
    """
    if not path.endswith('.ini'):
        raise ValueError("Selected file is not a configuration file. Try again.") 
    
    cfg = {}
    with open(path) as f: 
        for line in f: 
            if not line.__contains__('='):
                continue 
            key, value = line.split('=')
            cfg[key.strip()] = value.strip()
    
    return cfg


def load_module(target_module: str, filename: str, class_name: str) -> Any:
    """
    Loads a module given a filename, and class name.

    Parameters
    ----------
        target_module: str
            Target path to search for specified classes

        filename: str
            Filename to search for class

        class_name: str
            Class to search and load
    """

    spec = importlib.util.find_spec(target_module)
    module = importlib.util.module_from_spec(spec)
    sys.modules[filename] = module
    spec.loader.exec_module(module)

    k = getattr(module, class_name)
    return k


def get_configuration_files(path: str) -> Optional[List[str]]:
    """
    Returns configuration files found in specified path.

    Configuration filenames ends with .ini 

    Parameters
    ----------
        path:str
            Path in which search for configuration files are made. 
    """
    contents = os.listdir(path)
    if len(contents) == 0: 
        print(f"No files found in: {path}")
        return None
    
    configuration_files = [c for c in contents if c.endswith('.ini')]
    return configuration_files
