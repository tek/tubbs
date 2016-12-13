from ribosome.machine import message

StageI = message('StageI')
AObj = message('AObj', 'ident')
IObj = message('IObj', 'ident')
AObjRule = message('AObj', 'rule')
IObjRule = message('IObj', 'rule')
Select = message('Select', 'parser', 'tpe', 'ident')

__all__ = ('StageI', 'AObj', 'IObj', 'AObjRule', 'IObjRule', 'Select')
