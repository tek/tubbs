from ribosome.machine import message

StageI = message('StageI')
AObj = message('AObj', 'rule')
IObj = message('IObj', 'rule')

__all__ = ('StageI', 'AObj', 'IObj')
