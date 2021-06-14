from subprocess import Popen, PIPE, STDOUT
import logging
import traceback
import os 

log = logging.getLogger()


class ShellError(RuntimeError):
    '''raise this when there's a shell error'''


class ShellCmd(object):

    def __init__(self, cmd, name, silent=False, **kwargs):
        self._cmd = cmd
        self._name = name
        self._process = Popen(self._cmd, stdout=PIPE, stderr=STDOUT, universal_newlines=True)
        self.dupa = print(cmd)
        self._extra_args = kwargs
        self._silent = silent

    def wait(self):

        try:
            print(os.getcwd())
            for stdout_line in iter(self._process.stdout.readline, ""):
                if not self._silent:
                    log.info(dict(
                        command=self._cmd,
                        message=stdout_line,
                        **self._extra_args,
                    ))
                    
            self._process.stdout.close()
        except:
            log.error(dict(
                command=self._cmd,
                message='Error parsing cmd output: ' + str(self._name),
                stacktrace=traceback.format_exc(),
                **self._extra_args,
            ))

        errcode = self._process.wait()

        if errcode != 0:
            log.error(dict(
                command=self._cmd,
                message='Error: ' + str(self._name),
                error_code=errcode,
                **self._extra_args,
            ))
            error_msg = '{} exited with code {}'.format(self._name, errcode)
            raise ShellError(error_msg)


if __name__ == "__main__":
    print('in main')
    exclude_list = ShellCmd(
        cmd=[
            "ls", 
            os.path.join('/Users/kuba/Documents')
        ],
        name = 'test'
    )

    exclude_list.wait()
    print(exclude_list)