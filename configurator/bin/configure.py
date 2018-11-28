#! /usr/bin/env python3
# coding: utf8
import argparse
import codecs
import json
import os
import random
import string
import sys

from collections import OrderedDict

import jinja2


class Configurator:

    def __init__(self, **default_overrides):
        """
        Default values are read, in decreasing order of priority, from:
        - SETTING_<name> environment variable
        - Existing config file (in `default_overrides`)
        - Value passed to add()
        """
        self.__values = OrderedDict()
        self.__default_values = default_overrides
        try:
            self.__input = raw_input
        except NameError:
            self.__input = input

    def as_dict(self):
        return self.__values

    def mute(self):
        self.__input = None

    def get_default_value(self, name, default):
        setting_name = 'SETTING_' + name.upper()
        if os.environ.get(setting_name):
            return os.environ[setting_name]
        if name in self.__default_values:
            return self.__default_values[name]
        return default

    def add(self, name, default, question=""):
        default = self.get_default_value(name, default)

        if not self.__input or not question:
            return self.set(name, default)

        question += " (default: \"{}\"): ".format(default)
        return self.set(name, self.__input(question) or default)

    def add_bool(self, name, default, question=""):
        default = self.get_default_value(name, default)
        if default in [1, '1']:
            default = True
        if default in [0, '0', '']:
            default = False
        if not self.__input or not question:
            return self.set(name, default)
        question += " [Y/n] " if default else " [y/N] "
        while True:
            answer = self.__input(question)
            if answer is None or answer == '':
                return self.set(name, default)
            if answer.lower() in ['y', 'yes']:
                return self.set(name, True)
            if answer.lower() in ['n', 'no']:
                return self.set(name, False)

    def add_choice(self, name, default, choices, question=""):
        default = self.get_default_value(name, default)
        if not self.__input or not question:
            return self.set(name, default)
        question += " (default: \"{}\"): ".format(default)
        while True:
            answer = self.__input(question) or default
            if answer in choices:
                return self.set(name, answer)
            print("Invalid value. Choices are: {}".format(", ".join(choices)))

    def get(self, name):
        return self.__values.get(name)

    def set(self, name, value):
        self.__values[name] = value
        return self


def main():
    parser = argparse.ArgumentParser("Config file generator for Open edX")
    parser.add_argument('-c', '--config', default=os.path.join("/", "openedx", "config", "config.json"),
                        help="Load default values from this file. Config values will be saved there.")
    subparsers = parser.add_subparsers()

    parser_interactive = subparsers.add_parser('interactive')
    parser_interactive.add_argument('-s', '--silent', action='store_true',
                                    help=(
                                        "Be silent and accept all default values. "
                                        "This is good for debugging and automation, but "
                                        "probably not what you want"
                                    ))
    parser_interactive.set_defaults(func=interactive)

    parser_substitute = subparsers.add_parser('substitute')
    parser_substitute.add_argument('src', help="Template source directory")
    parser_substitute.add_argument('dst', help="Destination configuration directory")
    parser_substitute.set_defaults(func=substitute)

    args = parser.parse_args()
    args.func(args)

def load_config(args):
    if os.path.exists(args.config):
        with open(args.config) as f:
            return json.load(f)
    return {}

def interactive(args):
    print("\n====================================")
    print("      Interactive configuration ")
    print("====================================")

    configurator = Configurator(**load_config(args))
    if args.silent or os.environ.get('SILENT'):
        configurator.mute()
    configurator.add(
        'LMS_HOST', 'www.myopenedx.com', "Your website domain name for students (LMS)."
    ).add(
        'CMS_HOST', 'studio.' + configurator.get('LMS_HOST'), "Your website domain name for teachers (CMS)."
    ).add(
        'PLATFORM_NAME', "My Open edX", "Your platform name/title"
    ).add(
        'CONTACT_EMAIL', 'contact@' + configurator.get('LMS_HOST'), "Your public contact email address",
    ).add_choice(
        'LANGUAGE_CODE', 'en',
        ['en', 'am', 'ar', 'az', 'bg-bg', 'bn-bd', 'bn-in', 'bs', 'ca', 'ca@valencia', 'cs', 'cy', 'da', 'de-de', 'el', 'en-uk', 'en@lolcat', 'en@pirate', 'es-419', 'es-ar', 'es-ec', 'es-es', 'es-mx', 'es-pe', 'et-ee', 'eu-es', 'fa', 'fa-ir', 'fi-fi', 'fil', 'fr', 'gl', 'gu', 'he', 'hi', 'hr', 'hu', 'hy-am', 'id', 'it-it', 'ja-jp', 'kk-kz', 'km-kh', 'kn', 'ko-kr', 'lt-lt', 'ml', 'mn', 'mr', 'ms', 'nb', 'ne', 'nl-nl', 'or', 'pl', 'pt-br', 'pt-pt', 'ro', 'ru', 'si', 'sk', 'sl', 'sq', 'sr', 'sv', 'sw', 'ta', 'te', 'th', 'tr-tr', 'uk', 'ur', 'vi', 'uz', 'zh-cn', 'zh-hk', 'zh-tw'],
        "The default language code for the platform"
    ).add(
        'SECRET_KEY', random_string(24)
    ).add(
        'MYSQL_DATABASE', 'openedx'
    ).add(
        'MYSQL_USERNAME', 'openedx'
    ).add(
        'MYSQL_PASSWORD', random_string(8)
    ).add(
        'MONGODB_DATABASE', 'openedx'
    ).add(
        'NOTES_MYSQL_DATABASE', 'notes',
    ).add(
        'NOTES_MYSQL_USERNAME', 'notes',
    ).add(
        'NOTES_MYSQL_PASSWORD', random_string(8)
    ).add(
        'NOTES_SECRET_KEY', random_string(24)
    ).add(
        'NOTES_OAUTH2_SECRET', random_string(24)
    ).add(
        'XQUEUE_AUTH_USERNAME', 'lms'
    ).add(
        'XQUEUE_AUTH_PASSWORD', random_string(8)
    ).add(
        'XQUEUE_MYSQL_DATABASE', 'xqueue',
    ).add(
        'XQUEUE_MYSQL_USERNAME', 'xqueue',
    ).add(
        'XQUEUE_MYSQL_PASSWORD', random_string(8)
    ).add(
        'XQUEUE_SECRET_KEY', random_string(24)
    ).add_bool(
        'ACTIVATE_HTTPS', False, "Activate SSL/TLS certificates for HTTPS access? Important note: this will NOT work in a development environment.",
    ).add_bool(
        'ACTIVATE_NOTES', False, "Activate Student Notes service (https://open.edx.org/features/student-notes)?",
    ).add_bool(
        'ACTIVATE_PORTAINER', False, "Activate Portainer, a convenient Docker dashboard with a web UI (https://portainer.io)?",
    ).add_bool(
        'ACTIVATE_XQUEUE', False, "Activate Xqueue for external grader services? (https://github.com/edx/xqueue)",
    ).add(
        'ID', random_string(8)
    )

    # Save values
    with open(args.config, 'w') as f:
        json.dump(configurator.as_dict(), f, sort_keys=True, indent=4)
    print("\nConfiguration values were saved to ", args.config)


def substitute(args):
    config = load_config(args)

    for root, _, filenames in os.walk(args.src):
        for filename in filenames:
            if filename.startswith('.'):
                # Skip hidden files, such as files generated by the IDE
                continue
            src_file = os.path.join(root, filename)
            dst_file = os.path.join(args.dst, os.path.relpath(src_file, args.src))
            substitute_file(config, src_file, dst_file)

def substitute_file(config, src, dst):
    with codecs.open(src, encoding='utf-8') as fi:
        template = jinja2.Template(fi.read(), undefined=jinja2.StrictUndefined)
    try:
        substituted = template.render(**config)
    except jinja2.exceptions.UndefinedError as e:
        sys.stderr.write("ERROR Missing config value '{}' for template {}\n".format(e.args[0], src))
        sys.exit(1)

    dst_dir = os.path.dirname(dst)
    if not os.path.exists(dst_dir):
        os.makedirs(dst_dir)
    with codecs.open(dst, encoding='utf-8', mode='w') as fo:
        fo.write(substituted)

    # Set same permissions as original file
    os.chmod(dst, os.stat(src).st_mode)

    print("Generated file {} from template {}".format(dst, src))


def random_string(length):
    return "".join([random.choice(string.ascii_letters + string.digits) for _ in range(length)])

if __name__ == '__main__':
    main()
