from ribosome.machine import message, json_message

StageI = message('StageI')
AObj = message('AObj', 'ident')
IObj = message('IObj', 'ident')
AObjRule = message('AObj', 'rule')
IObjRule = message('IObj', 'rule')
Select = message('Select', 'parser', 'tpe', 'ident')
Format = message('Format', 'parser', 'range')
FormatRange = json_message('FormatRange')
FormatAt = json_message('FormatAt', 'line')
FormatExpr = json_message('FormatExpr', 'line', 'count')

__all__ = ('StageI', 'AObj', 'IObj', 'AObjRule', 'IObjRule', 'Select',
           'Format', 'FormatRange', 'FormatAt', 'FormatExpr')
