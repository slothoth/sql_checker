import json
from threading import Lock
import os
import sys


class ResourceLoader:
    _instance = None
    _lock = Lock()
    node_templates = {}
    possible_vals = {}
    _files = {}

    def __new__(cls):
        if not cls._instance:
            with cls._lock:
                if not cls._instance:
                    cls._instance = super().__new__(cls)
                    cls._instance._load_resources()
        return cls._instance

    def _load_resources(self):
        self._files = {
            'node_templates': self.resource_path("resources/db_spec.json"),
            'possible_vals': self.resource_path('resources/db_possible_vals.json'),
            'all_possible_vals': self.resource_path('resources/all_possible_vals.json')
        }
        self.node_templates = self._read_file(self._files['node_templates'])
        self.possible_vals = self._read_file(self._files['possible_vals'])
        self.all_possible_vals = self._read_file(self._files['all_possible_vals'])

    @staticmethod
    def _read_file(path):
        with open(path, 'r') as f:
            return json.load(f)

    @staticmethod
    def _write_file(path, data):
        with open(path, 'w') as f:
            json.dump(data, f, indent=2)

    def update_node_templates(self, data):
        self.node_templates = data
        self._write_file(self._files['node_templates'], data)

    def update_possible_vals(self, data):
        self.possible_vals = data
        self._write_file(self._files['possible_vals'], data)

    def update_all_vals(self, data):
        self.all_possible_vals = data
        self._write_file(self._files['all_possible_vals'], data)

    @staticmethod
    def resource_path(relative_path):
        base_path = getattr(sys, "_MEIPASS", os.path.abspath("."))
        return os.path.join(base_path, relative_path)