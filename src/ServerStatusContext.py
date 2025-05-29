#!/usr/bin/python
# -*- coding:utf-8 -*-

import argparse
from dataclasses import dataclass

RENDERER_TYPE_EPAPER = 'epaper'
RENDERER_TYPE_CONSOLE = 'console'
ARG_RENDERER_CHOICES = [RENDERER_TYPE_EPAPER, RENDERER_TYPE_CONSOLE]
ARG_PAGE_CHOICES = ['1', '2']

@dataclass
class Context:
    default_page: int
    render_type: str

    def __str__(self):
        return f"default_page: {self.default_page}, render_type: {self.render_type}"

class ServerStatusContext:
    context = Context(1, RENDERER_TYPE_EPAPER)

    @staticmethod
    def parse_arguments():
        parser = argparse.ArgumentParser(description='Server Status Display')
        parser.add_argument('-r', '--renderer', choices=ARG_RENDERER_CHOICES, default='epaper',
                            help='Choose renderer type: console or epaper')
        parser.add_argument('-p', '--page', choices=ARG_PAGE_CHOICES, default=1,
                            help='Choose default page nr: 1 or 2')

        args = parser.parse_args()

        ServerStatusContext.context = Context(int(args.page), args.renderer)
