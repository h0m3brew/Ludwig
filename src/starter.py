import csv
import datetime
import shutil
from termcolor import cprint
import socket

from src import config


class Starter:
    """
    Contains methods for reading configs from disk, checking, and supplying configs for NN training.
    """

    def __init__(self,
                 reps,
                 default_configs_dict,
                 check_fn,
                 logger):
        self.reps = reps
        self.default_configs_dict = default_configs_dict
        self.check_fn = check_fn
        self.logger = logger

    @staticmethod
    def to_flavor(model_name):
        flavor = model_name.split('_')[1]
        return flavor

    @staticmethod
    def make_model_name(flavor):
        time_of_init = datetime.datetime.now().strftime('%m-%d-%H-%M-%S')
        hostname = socket.gethostname()
        model_name = '{}_{}_{}'.format(hostname, time_of_init, flavor)
        # remove any existing dir with same name
        path = config.Dirs.runs / model_name
        if path.is_dir():
            shutil.rmtree(str(config.Dirs.runs / model_name))
        return model_name

    @staticmethod
    def to_correct_type(value):
        if value.isdigit():
            value = int(value)
        elif value == 'None':
            value = None
        elif '.' in value:
            value = float(value)
        else:
            value = str(value)
        return value

    @staticmethod
    def make_new_configs_dicts():
        p = config.Dirs.user / 'configs.csv'
        if not p.exists():
            print('Did not find configs.csv in {}'.format(p))
        new_configs_dicts = list(csv.DictReader(p.open('r')))
        # printout
        print('New configs:')
        for config_id, d in enumerate(new_configs_dicts):
            print('Config {}:'.format(config_id))
            for k, v in sorted(d.items()):
                print('{:>20} -> {:<20}'.format(k, v))
        return new_configs_dicts

    def make_checked_configs_dicts(self, new_configs_dicts):
        configs_dicts = []
        new_config_names = set()
        for new_configs_dict in new_configs_dicts:
            configs_dict = self.default_configs_dict.copy()
            # overwrite
            for config_name, config_value in new_configs_dict.items():
                if config_name not in self.default_configs_dict.keys():
                    raise Exception('"{}" is not a valid config.'.format(config_name))
                else:
                    configs_dict[config_name] = self.to_correct_type(config_value)
                    new_config_names.add(config_name)
            # add configs_dict
            self.check_fn(configs_dict, new_config_names)
            configs_dicts.append(configs_dict)
        return configs_dicts

    def gen_configs_dicts(self):
        # parse + check
        new_configs_dicts = self.make_new_configs_dicts()
        checked_config_dicts = self.make_checked_configs_dicts(new_configs_dicts)
        # generate
        for config_id, configs_dict in enumerate(checked_config_dicts):
            cprint('==================================', 'blue')
            # make num_times_train
            num_times_logged = 0
            num_times_logged += self.count_num_times_logged(configs_dict)
            num_times_train = self.reps - num_times_logged
            cprint('Config {} logged {} times'.format(config_id, num_times_logged), 'blue')
            # generate
            num_times_train = max(0, num_times_train)
            color = 'green' if num_times_train > 0 else 'blue'
            cprint('Will train Config {} {} times'.format(config_id, num_times_train), color)
            cprint('==================================', 'blue')
            if num_times_train > 0:
                for _ in range(num_times_train):
                    # timestamp
                    configs_dict['model_name'] = self.make_model_name(configs_dict['flavor'])
                    yield configs_dict

    def count_num_times_logged(self, configs_dict):
        num_times_logged = 0
        try:
            log_entry_dicts = self.logger.load_log()
        except IOError:
            return 0
        if not log_entry_dicts:
            return 0
        # make num_times_logged
        for log_entry_d in log_entry_dicts:
            if log_entry_d['timepoint'] != log_entry_d['num_saves']:
                continue
            else:
                bool_list = []
                for config_name, config_value in configs_dict.items():
                    if config_name == 'model_name':
                        continue
                    try:
                        bool_list.append(config_value == log_entry_d[config_name])
                    except KeyError:
                        print('WARNING: config {} not found in main log'.format(config_name))
                        pass
                if all(bool_list):
                    num_times_logged += 1
        return num_times_logged
