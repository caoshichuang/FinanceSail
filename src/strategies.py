"""
交易策略系统
- StrategyLoader: 从 YAML 文件加载策略定义
- SkillManager: 管理策略激活和优先级
"""

from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional

try:
    from loguru import logger
except ImportError:
    import logging

    logger = logging.getLogger(__name__)

# 内置策略目录
DEFAULT_STRATEGY_DIR = Path(__file__).parent.parent / "strategies"


@dataclass
class TradingStrategy:
    """交易策略定义"""

    name: str
    display_name: str
    description: str
    instructions: str
    category: str = "general"
    version: str = "1.0"
    author: str = "unknown"
    core_rules: List[int] = field(default_factory=list)
    required_tools: List[str] = field(default_factory=list)
    source_file: str = ""

    def to_prompt_section(self) -> str:
        """生成可注入到 Prompt 的策略说明段"""
        return f"## 策略：{self.display_name}\n\n{self.instructions}"


class StrategyLoader:
    """
    YAML 策略文件加载器
    支持内置目录和自定义目录
    """

    def __init__(self, strategy_dirs: Optional[List[Path]] = None):
        """
        Args:
            strategy_dirs: 策略目录列表（默认包含内置 strategies/）
        """
        self._dirs: List[Path] = [DEFAULT_STRATEGY_DIR]

        if strategy_dirs:
            for d in strategy_dirs:
                if d.exists() and d.is_dir():
                    self._dirs.append(d)
                else:
                    logger.warning(f"策略目录不存在，跳过: {d}")

    def load_all(self) -> Dict[str, TradingStrategy]:
        """
        加载所有策略文件

        Returns:
            Dict[str, TradingStrategy]: 策略名称 → 策略对象
        """
        strategies: Dict[str, TradingStrategy] = {}

        for strategy_dir in self._dirs:
            if not strategy_dir.exists():
                continue
            for yaml_file in sorted(strategy_dir.glob("*.yaml")):
                strategy = self._load_file(yaml_file)
                if strategy:
                    # 自定义目录优先级高（后加载覆盖前）
                    strategies[strategy.name] = strategy

        logger.info(
            f"策略加载完成，共 {len(strategies)} 个策略: {list(strategies.keys())}"
        )
        return strategies

    def _load_file(self, yaml_file: Path) -> Optional[TradingStrategy]:
        """
        加载单个 YAML 策略文件

        Args:
            yaml_file: YAML 文件路径

        Returns:
            TradingStrategy 或 None（加载失败时）
        """
        try:
            import yaml

            with open(yaml_file, "r", encoding="utf-8") as f:
                data = yaml.safe_load(f)

            if not isinstance(data, dict):
                logger.warning(f"策略文件格式错误（非字典）: {yaml_file}")
                return None

            # 校验必填字段
            for required in ("name", "display_name", "instructions"):
                if required not in data:
                    logger.warning(f"策略文件缺少必填字段 '{required}': {yaml_file}")
                    return None

            strategy = TradingStrategy(
                name=data["name"],
                display_name=data["display_name"],
                description=data.get("description", ""),
                instructions=data["instructions"],
                category=data.get("category", "general"),
                version=str(data.get("version", "1.0")),
                author=data.get("author", "unknown"),
                core_rules=data.get("core_rules", []),
                required_tools=data.get("required_tools", []),
                source_file=str(yaml_file),
            )
            logger.debug(f"加载策略: {strategy.name} ({yaml_file.name})")
            return strategy

        except Exception as e:
            logger.warning(f"策略文件加载失败 {yaml_file}: {e}")
            return None


class SkillManager:
    """
    策略管理器（单例）
    - 管理所有已加载策略
    - 支持激活/停用策略
    - 生成组合 Prompt 片段
    """

    _instance: Optional["SkillManager"] = None

    def __new__(cls) -> "SkillManager":
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return
        self._initialized = True
        self._strategies: Dict[str, TradingStrategy] = {}
        self._active: List[str] = []
        self._load_strategies()

    def _load_strategies(self):
        """加载所有策略"""
        # 检查是否有自定义策略目录
        custom_dirs = []
        try:
            from src.config.settings import settings

            custom_dir = getattr(settings, "AGENT_SKILL_DIR", None)
            if custom_dir:
                custom_dirs.append(Path(custom_dir))
        except Exception:
            pass

        loader = StrategyLoader(strategy_dirs=custom_dirs if custom_dirs else None)
        self._strategies = loader.load_all()

        # 从配置加载默认激活策略
        try:
            from src.config.settings import settings

            active_skills = getattr(settings, "AGENT_SKILLS", [])
            if isinstance(active_skills, str):
                active_skills = [
                    s.strip() for s in active_skills.split(",") if s.strip()
                ]
            for skill in active_skills:
                if skill in self._strategies:
                    self._active.append(skill)
                else:
                    logger.warning(f"配置的策略 '{skill}' 未找到，跳过")
        except Exception:
            # 默认激活 bull_trend
            if "bull_trend" in self._strategies:
                self._active = ["bull_trend"]

        if not self._active and self._strategies:
            # 至少激活第一个策略
            self._active = [next(iter(self._strategies))]

        logger.info(f"已激活策略: {self._active}")

    @property
    def all_strategies(self) -> Dict[str, TradingStrategy]:
        return self._strategies.copy()

    @property
    def active_strategies(self) -> List[TradingStrategy]:
        return [
            self._strategies[name] for name in self._active if name in self._strategies
        ]

    def activate(self, name: str):
        """激活策略"""
        if name not in self._strategies:
            raise ValueError(f"策略 '{name}' 不存在")
        if name not in self._active:
            self._active.append(name)
            logger.info(f"策略已激活: {name}")

    def deactivate(self, name: str):
        """停用策略"""
        if name in self._active:
            self._active.remove(name)
            logger.info(f"策略已停用: {name}")

    def get_combined_prompt(self) -> str:
        """
        获取所有激活策略的组合 Prompt 片段

        Returns:
            str: 可直接注入 system prompt 的策略说明
        """
        active = self.active_strategies
        if not active:
            return ""

        sections = [s.to_prompt_section() for s in active]
        return "\n\n---\n\n".join(sections)

    def get_strategy(self, name: str) -> Optional[TradingStrategy]:
        return self._strategies.get(name)

    def reload(self):
        """热重载策略"""
        self._active = []
        self._initialized = False
        self.__init__()


# 全局策略管理器实例
skill_manager = SkillManager()
