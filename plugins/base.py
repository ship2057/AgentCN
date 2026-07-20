"""
插件接口定义（AgentCN v0.0.2607）
"""
from abc import ABC, abstractmethod

class IPlugin(ABC):
    @property
    @abstractmethod
    def name(self) -> str:
        ...

    @abstractmethod
    def execute(self, params: dict, context: dict) -> str:
        ...