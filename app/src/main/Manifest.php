<?php

class Manifest {
    const ROOT_PACKAGE = "";  # !!! Don't Change This Line !!!

    private const LIBS = [
        'dir_path' => '../../libs',
        'lib1' => [
		// your lib files here
        ]
	'libn' => [
		// your other lib files here
        ]
    ];

    private const DATABASE = [
        'dir_path' => './php/database',
        'tables' => [
		// your tables here
        ],
        'entities' => [
		// your entities here	
        ],
        'dao' => [
		// your dao here
        ],
        'db' => [
            'main_database'
        ]
    ];

    private const Models = [
      'dir_path' => './php',
      'models' => [
	// your models here
      ]
    ];

    private const Repository = [
        'dir_path' => './php',
        'repository' => [
		// your repository file here
        ]
    ];

    private const CORE = [
        'dir_path' => './php/core',
        'base_core' => [
		// your base core here
       	],
        'aggregate_core' => [
		// your aggregate core here
        ]
    ];

    private const PLUGINS = [
        'dir_path' => './php',
        'plugins' => [
		// your plugins here
        ]
    ];

    private const UTILS = [
        'dir_path' => './php/utils'
    ];

    private const ADAPTERS = [
        'dir_path' => './php/adapters'
    ];

    private const VIEWS = [
        'dir_path' => './php/views',
        'fragments' => [
        ],
        'activities' => [
        ]
    ];

    private const DI_PATH = './php/di';
    private const BUILD_GENERATED_CLASSES_DIR_PATH = "../../build/generated";

    public static function getAppSystemRoot(): string {
        return substr(self::devisePath('../../../'), 0, -1);
    }

    public static function devisePath($path): string {
        $root_path = explode('/', __DIR__);

        if (substr($path, 0, 2) === './') {
            $path = substr($path, 2);
        } else {
            while (substr($path, 0, 3) === '../') {
                $path = substr($path, 3);
                array_pop($root_path);
            }
        }

        return implode('/', $root_path) . '/' . $path;
    }

    private function requireItems(array $package) {
        foreach ($package as $key => $value) {
            if ($key !== 'dir_path') {
                foreach ($value as $module) {
                    $path = $package['dir_path'] . ($package['dir_path'] === './' ? '' : '/') . $key . '/' . $module . '.php' . '';
                    require self::devisePath($path) . '';
                }
            }
        }
    }

    private function loadRequirements() {
        self::requireItems(self::LIBS);
        self::requireItems(self::DATABASE);
        self::requireItems(self::Models);
        self::requireItems(self::Repository);

        foreach(glob(self::devisePath(self::DI_PATH).'/*.php') as $file) {
            require $file . '';
        }

        foreach(glob(self::devisePath(self::BUILD_GENERATED_CLASSES_DIR_PATH).'/*.php') as $file) {
            require $file . '';
        }

        self::requireItems(self::CORE);
        self::requireItems(self::PLUGINS);
        self::requireItems(self::UTILS);
        self::requireItems(self::ADAPTERS);
        self::requireItems(self::VIEWS);
    }

    private function __construct() {
        $this->loadRequirements();
    }

    public static function create() {
        new Manifest();
    }
}

Manifest::create();
