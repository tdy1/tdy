from __future__ import annotations
from dataclasses import dataclass
from decimal import Decimal
from typing import Callable, Mapping

@dataclass(frozen=True)
class SensitivityResult:
    variable: str
    value: Decimal
    outputs: Mapping[str,Decimal]

def run_one_way(base:Mapping[str,Decimal], variable:str, values:list[Decimal], calculator:Callable[[Mapping[str,Decimal]],Mapping[str,Decimal]])->list[SensitivityResult]:
    if variable not in base: raise KeyError(variable)
    out=[]
    for value in values:
        x=dict(base); x[variable]=value
        out.append(SensitivityResult(variable,value,calculator(x)))
    return out
