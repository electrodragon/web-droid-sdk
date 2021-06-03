#!/usr/bin/env python3

import os
import yaml


class Argument:

    def __init__(self, name, meta_data):
        self.data_type = None
        self.default_value = None
        self.comparison_suffix = None
        self.name = name
        self.initMetaData(meta_data)

    def initMetaData(self, meta_data):
        if isinstance(meta_data, str):  # If meta data in in form of string
            if ',' in meta_data:
                tmp = meta_data.split(',')
                self.data_type = tmp[0].strip()
                self.default_value = ','.join(tmp[1:]).strip()
            else:
                self.data_type = meta_data
        else:  # If meta data is in form of dictionary
            self.data_type = meta_data['type']
            if 'default' in meta_data:
                self.default_value = meta_data['default']
            if 'true-comparison' in meta_data:
                self.comparison_suffix = meta_data['true-comparison']

    def formatNameAsField(self):
        self.name = self.name.replace('-', '_').replace(' ', '_').replace('.', '_').lower()
        if '_' in self.name:
            chunk = self.name.split('_')
            for i in range(len(chunk[1:])):
                chunk[i + 1] = chunk[i + 1].capitalize()
            self.name = ''.join(chunk)

    def getAsPublicField(self):
        res = f'public {"?" if self.default_value == "null" else ""}{self.data_type} ${self.name}'
        if self.default_value is not None:
            res = res + " = "
            if self.data_type == 'string' and self.default_value != 'null':
                res = res + '\"{}\"'.format(self.default_value)
            else:
                res = res + '{}'.format(self.default_value)
        return '{}{};\n'.format(' ' * 4, res)


class IfElse:

    def __init__(self, indent=8):
        self.if_started = False
        self.code = list()
        self.nested_if_count = 0
        self.indent = indent

    def iF(self, condition):
        if self.if_started:  # Nested If
            self.nested_if_count = self.nested_if_count + 1
        self.code.append('{}if ({}) {{\n'.format(' ' * self.getIndent(), condition))
        self.if_started = True

    def elIf(self, condition):
        self.code.append('{}}} elseif ({}) {{\n'.format(' ' * self.getIndent(), condition))

    def el(self):
        self.code.append('{}}} else {{\n'.format(' ' * self.getIndent()))

    def body(self, statement):
        self.code.append('{}{};\n'.format(' ' * (self.getIndent() + 4), statement))

    def getIndent(self):
        if self.nested_if_count > 0:
            return self.indent + (self.nested_if_count * 4)
        return self.indent

    def fi(self):
        self.code.append('{}}}\n'.format(' ' * self.getIndent()))
        if self.nested_if_count > 0:
            self.nested_if_count = self.nested_if_count - 1
        else:
            self.if_started = False

    def getCode(self):
        return self.code


class Constructor:

    def __init__(self):
        self.constructor_params = list()
        self.code = list()

    def constructorParams(self, params):
        self.constructor_params = params

    def addCodeLines(self, code):
        for lin in code:
            self.code.append(lin)

    def initVariable(self, variable_name, initializer_statement, indent=8):
        self.code.append('{}$this->{} = {};\n'.format(' ' * indent, variable_name, initializer_statement))

    def getConstructorCode(self):
        constructor = f'\n{" " * 4}function __construct('
        if len(self.constructor_params) > 0:
            for i in range(len(self.constructor_params)):
                self.constructor_params[i] = '${}'.format(self.constructor_params[i])
            constructor = constructor + ', '.join(self.constructor_params)
        constructor = constructor + ') {\n'
        constructor = constructor + ''.join(self.code)
        return constructor + '{}}}\n'.format(' ' * 4)


class Constant:

    def __init__(self, name, value, reformat=True):
        self.name = name
        self.value = value
        if reformat:
            self.name = self.name.replace('-', '_').replace(' ', '_').upper()


class ClassFactory:

    def __init__(self, class_name=None):
        self.constants = list()
        self.public_fields = list()
        self.constructor = None
        self.class_name = class_name

    def setClassName(self, class_name):
        self.class_name = class_name

    def addPublicField(self, argument):
        self.public_fields.append(argument)

    def addConstant(self, constant):
        self.constants.append(constant)  # Add to Constants List as a Tuple

    def setConstructor(self, constructor):
        self.constructor = constructor  # Sets already built Constructor to This Class

    def writeClassIn(self, file):
        file.write('\n\nclass {} {{\n'.format(self.class_name))

        if len(self.constants) > 0:
            for constant in self.constants:  # Constant and constant Value
                file.write('{}const {} = "{}";\n'.format(' ' * 4, constant.name, constant.value))

        if len(self.public_fields) > 0:
            for field in self.public_fields:
                file.write(field.getAsPublicField())

        if self.constructor is not None:
            file.write(self.constructor.getConstructorCode())

        file.write('}\n')


class BuildConfig:

    def __init__(self, meta_data):
        for meta in meta_data:
            for config_type in meta:
                if config_type == 'RELEASE_CONFIG':
                    for config_item in meta[config_type]:
                        for config_name, value in config_item.items():
                            print(config_name, value)
                            if config_name == 'DB_HOSTNAME':
                                self.release_db_host = value
                            elif config_name == 'DB_USERNAME':
                                self.release_db_username = value
                            elif config_name == 'DB_PASSWORD':
                                self.release_db_password = value
                            elif config_name == 'DB_NAME':
                                self.release_db_name = value
                            elif config_name == 'ROOT_PACKAGE':
                                self.release_root_pkg = value
                elif config_type == 'LOCAL_CONFIG':
                    for config_item in meta[config_type]:
                        for config_name, value in config_item.items():
                            print(config_name, value)
                            if config_name == 'DB_HOSTNAME':
                                self.local_db_host = value
                            elif config_name == 'DB_USERNAME':
                                self.local_db_username = value
                            elif config_name == 'DB_PASSWORD':
                                self.local_db_password = value
                            elif config_name == 'DB_NAME':
                                self.local_db_name = value
                            elif config_name == 'ROOT_PACKAGE':
                                self.local_root_pkg = value

        self.release_manifest_content = []
        self.local_manifest_content = []
        self.release_db_content = []
        self.local_db_content = []

    def addManifestConfigLine(self, code, caution=False):
        release_code = code['release']
        local_code = code['local']
        if caution:
            code['release'] = f'{release_code}  # !!! Don\'t Change This Line !!!'
            code['local'] = f'{local_code}  # !!! Don\'t Change This Line !!!'
        self.release_manifest_content.append('{}{}\n'.format(' ' * 4, code['release']))
        self.local_manifest_content.append('{}{}\n'.format(' ' * 4, code['local']))

    def addManifestLine(self, code):
        self.release_manifest_content.append(code)
        self.local_manifest_content.append(code)

    def addDatabaseConfigLine(self, code, caution=False):
        release_code = code['release']
        local_code = code['local']
        if caution:
            code['release'] = f'{release_code}  # !!! Don\'t Change This Line !!!'
            code['local'] = f'{local_code}  # !!! Don\'t Change This Line !!!'
        self.release_db_content.append('{}{}\n'.format(' ' * 4, code['release']))
        self.local_db_content.append('{}{}\n'.format(' ' * 4, code['local']))

    def addDatabaseLine(self, code):
        self.release_db_content.append(code)
        self.local_db_content.append(code)


def capitalizeEachAndRemovePhpExtension(chunks):
    for i in range(len(chunks)):
        chunks[i] = chunks[i].capitalize()
        if '.php' in chunks[i]:
            chunks[i] = chunks[i].replace('.php', '')
    return chunks


if __name__ == '__main__':

    with open('app/build/generated/generated_classes.php', 'w+') as gc:  # Generated Code File (GC)
        gc.write('<?php')

        """ GENERATING NavAction """
        navActionClass = ClassFactory('NavAction')
        for f in os.listdir('app/src/main/res/layout'):
            name_chunks = capitalizeEachAndRemovePhpExtension(f.split('_'))

            if 'Activity' in name_chunks:
                name_chunks.remove('Activity')
                name_chunks.append('Activity')

            navActionClass.addConstant(Constant(''.join(name_chunks), f, False))  # MainActivity => activity_main.php
        navActionClass.writeClassIn(gc)

        """ GENERATING Drawable """
        drawableClass = ClassFactory('Drawable')
        for f in os.listdir('app/src/main/res/drawable'):
            drawableClass.addConstant(Constant('_'.join(f.split('.')[:-1]).lower(), f, False))
        drawableClass.writeClassIn(gc)

        """ GENERATING Agent """
        agentClass = ClassFactory('Agent')
        for f in os.listdir('app/src/main/php/agents'):
            agentClass.addConstant(Constant(''.join(capitalizeEachAndRemovePhpExtension(f.split('_'))), f, False))
        agentClass.writeClassIn(gc)

        """ GENERATING SessionKey """
        sessionKeyClass = ClassFactory('SessionKey')
        with open('app/src/main/res/values/session_keys.yaml', 'r') as session_keys_file:
            for k in yaml.full_load(session_keys_file):
                sessionKeyClass.addConstant(Constant(k, k, False))
        sessionKeyClass.writeClassIn(gc)

        """ GENERATING Text """
        textClass = ClassFactory('Text')
        with open('app/src/main/res/values/texts.yaml', 'r') as texts_file:
            for k, v in yaml.full_load(texts_file).items():
                textClass.addConstant(Constant(k, v, False))
        textClass.writeClassIn(gc)

        """ GENERATING Style """
        styleSheetsClass = ClassFactory('Style')
        for f in os.listdir('app/src/main/res/values/styles'):
            styleSheetsClass.addConstant(Constant('_'.join(f.split('.')[:-1]).lower(), f, False))
        styleSheetsClass.writeClassIn(gc)

        """ GENERATING JavaScript Class """
        javaScriptClass = ClassFactory('JavaScript')
        for f in os.listdir('app/src/main/javascript'):
            javaScriptClass.addConstant(Constant('_'.join(f.split('.')[:-1]).lower(), f, False))
        javaScriptClass.writeClassIn(gc)

        with open('app/src/main/res/safe_args/safe_args.yaml', 'r') as safe_args_file:
            for class_item in yaml.full_load(safe_args_file):
                classArg = ClassFactory()
                classArgs = ClassFactory()
                ifi = IfElse()
                constructor = Constructor()
                print(class_item)
                for class_name in class_item:
                    classArg.setClassName(f'{class_name}Arg')  # Create Arg Class
                    classArgs.setClassName(f'{class_name}Args')  # Create Args Class
                    method = class_item[class_name]['method']  # Method GET POST
                    print(method)
                    forLaterConstructorUsage = []
                    for argument in class_item[class_name]['arguments']:  # All Arguments
                        for argument_name in argument:
                            constant = Constant(argument_name, argument_name)
                            public_field = Argument(argument_name, argument[argument_name])
                            public_field.formatNameAsField()
                            classArg.addConstant(constant)
                            classArgs.addPublicField(public_field)
                            if public_field.default_value is None:  # Die if not passed
                                ifi.iF(f'!isset($_{method}[{classArg.class_name}::{constant.name}])')
                                ifi.body('die()')
                                ifi.fi()
                            forLaterConstructorUsage.append((constant, public_field))

                    constructor.addCodeLines(ifi.getCode())
                    for constant, public_field in forLaterConstructorUsage:
                        init_statement = f'$_{method}[{classArg.class_name}::{constant.name}]'
                        if public_field.default_value is not None:
                            ifi2 = IfElse()
                            ifi2.iF(f'isset($_{method}[{classArg.class_name}::{constant.name}])')

                            statement = f'$this->{public_field.name} ='
                            if public_field.data_type == 'int':
                                statement = f'{statement} (int) {init_statement}'
                            else:
                                statement = f'{statement} {init_statement}'

                            if public_field.data_type == 'bool' and public_field.comparison_suffix is not None:
                                ifi2.body(f'{statement} {public_field.comparison_suffix}')
                            else:
                                ifi2.body(statement)
                            ifi2.fi()
                            constructor.addCodeLines(ifi2.getCode())
                        else:
                            if public_field.data_type == 'int':
                                init_statement = f'(int) {init_statement}'
                            if public_field.data_type == 'bool' and public_field.comparison_suffix is not None:
                                init_statement = f'{init_statement} {public_field.comparison_suffix}'
                            constructor.initVariable(public_field.name, init_statement)
                    classArgs.setConstructor(constructor)
                classArg.writeClassIn(gc)
                classArgs.writeClassIn(gc)

        with open('app/src/main/res/values/build_config.yaml', 'r') as build_config:
            config = BuildConfig(yaml.full_load(build_config))

            with open('app/src/main/Manifest.php', 'r') as manifest:
                for line in manifest.readlines():
                    if 'const ROOT_PACKAGE' in line:
                        config.addManifestConfigLine({
                            'release': f'const ROOT_PACKAGE = "{config.release_root_pkg}";',
                            'local': f'const ROOT_PACKAGE = "{config.local_root_pkg}";'
                        }, True)
                    else:
                        config.addManifestLine(line)

    with open('app/src/main/php/database/db/Your_Database_Here.php', 'r') as db_content:
        for line in db_content.readlines():
            if 'const HOSTNAME' in line:
                config.addDatabaseConfigLine({
                    'release': f'const HOSTNAME = "{config.release_db_host}";',
                    'local': f'const HOSTNAME = "{config.local_db_host}";'
                }, True)
            elif 'const USERNAME' in line:
                config.addDatabaseConfigLine({
                    'release': f'const USERNAME = "{config.release_db_username}";',
                    'local': f'const USERNAME = "{config.local_db_username}";'
                }, True)
            elif 'const PASSWORD' in line:
                config.addDatabaseConfigLine({
                    'release': f'const PASSWORD = "{config.release_db_password}";',
                    'local': f'const PASSWORD = "{config.local_db_password}";'
                }, True)
            elif 'const DATABASE' in line:
                config.addDatabaseConfigLine({
                    'release': f'const DATABASE = "{config.release_db_name}";',
                    'local': f'const DATABASE = "{config.local_db_name}";'
                }, True)
            else:
                config.addDatabaseLine(line)
    release_dir = 'app/build/outputs/release'
    os.system(f'if [ -d "app/build/outputs" ]; then rm -rf app/build/outputs; fi')
    os.system('tar -cvf app.tar app index.php')
    os.system(f'mkdir -p {release_dir}')
    os.system(f'mv app.tar {release_dir}/ && cd {release_dir} && tar -xvf app.tar && rm app.tar')
    os.system(f'rm -rf {release_dir}/app/src/main/res/safe_args')
    os.system(f'rm -rf {release_dir}/app/src/main/res/values/build_config.yaml')
    os.system(f'rm -rf {release_dir}/app/src/main/res/values/session_keys.yaml')
    os.system(f'rm -rf {release_dir}/app/src/main/res/values/texts.yaml')
    with open(f'{release_dir}/app/src/main/Manifest.php', 'w+') as f:
        for line in config.release_manifest_content:
            f.write(line)
    with open(f'{release_dir}/app/src/main/php/database/db/Your_Database_here.php', 'w+') as f:
        for line in config.release_db_content:
            f.write(line)
    os.system(f'cd {release_dir} && 7z a release_build.zip app index.php')  # Create ZiP
    os.system(f'rm -rf {release_dir}/app {release_dir}/index.php')  # Remove Release Files After Zipping
    with open('app/src/main/Manifest.php', 'w+') as f:
        for line in config.local_manifest_content:
            f.write(line)
    with open('app/src/main/php/database/db/Your_Database_here.php', 'w+') as f:
        for line in config.local_db_content:
            f.write(line)

