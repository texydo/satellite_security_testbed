import random


class Command:
    """
    A class to represent a command with a name, duration, and frequency.
    """

    def __init__(self,command_item, name = None, command_duration = None, command_frequency = None):
        """
        Initializes a new Command instance.
        """
        if command_item == None: 
            self.name = name
            self.duration = command_duration
            self.frequency = command_frequency
        else:
            self.name = command_item['command']
            
            duration_range = Command.parse_range(command_item['duration'])
            frequency_range = Command.parse_range(command_item['frequency'])
                
                # Choose random duration and frequency within the specified ranges
            duration = random.randint(duration_range[0], duration_range[1])
            frequency = random.randint(frequency_range[0], frequency_range[1])  # Ensure frequency is an integer
            
            self.duration = duration
            self.frequency = frequency

            # Save the lower and upper limit of both the frequency and the duration.
            self.min_duration, self.max_duration = duration_range[0], duration_range[1]
            self.min_frequency, self.max_frequency = frequency_range[0], frequency_range[1]
    
    def create_unified_command(self):
        """
        Formats a command into a standardized format by adjusting spaces around the command's components.

        This static method takes a command as input, which is expected to be a string consisting of space-separated words. It identifies the lengths of the first two words (assumed to represent the module and command type) and calculates the necessary padding to align these components within a fixed-width format. The method then constructs a unified command string by concatenating the original words with calculated spaces inserted between them. The resulting string adheres to a predefined format, enhancing readability and consistency across different commands.

        Args:
            command (str): The command to be formatted, consisting of space-separated words.

        Returns:
        
            str: The formatted command string, aligned according to the predefined format.

        Note:
            This method assumes that the command consists of at least four words, with the first word representing the module and the second word representing the command type. The exact alignment and spacing may vary depending on the specific requirements of the application or system using this method.
        """
        unified_command = ""
        
        
        words = self.name.split()
        
        module_len = len(words[0])
        type_len = len(words[1]) 
        
        first_space = (11 - module_len) * " "
        second_space = (4 - type_len) * " "
        
        if   len(words) == 4: unified_command = words[0] + first_space + words[1] + second_space + words[2] + " " + words[3]
        elif len(words) == 3: unified_command = words[0] + first_space + words[1] + second_space + words[2] #This line is for command with no arguments. for example the COM commands.
        
        return unified_command
    
    @staticmethod
    def parse_range(range_str):
        """Parse a list representing a range into a tuple of integers."""
        if len(range_str)!= 2:
            raise ValueError("Range must contain exactly two elements.")
        start, end = map(int, range_str)
        return (start, end)
    
    def set_rnd_duration_and_frequency(self):
        self.duration =  random.randint(self.min_duration, self.max_duration)
        self.frequency = random.randint(self.min_frequency, self.max_frequency)
        
        