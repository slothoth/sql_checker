from typing import Optional

from sqlalchemy import Boolean, Column, ForeignKey, Integer, REAL, Table, Text, text
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship

class Base(DeclarativeBase):
    pass


t_AdvancedStartArmyUnits = Table(
    'AdvancedStartArmyUnits', Base.metadata,
    Column('Age', Text, nullable=False),
    Column('ArmyID', Integer, nullable=False),
    Column('Level', Integer, nullable=False, server_default=text('0')),
    Column('Unit', Text, nullable=False)
)
# Types and Kinds first

class Kinds(Base):
    __tablename__ = 'Kinds'

    Kind: Mapped[str] = mapped_column(Text, primary_key=True)
    Hash: Mapped[int] = mapped_column(Integer, nullable=False, server_default=text('0'))

    Types: Mapped[list['Types']] = relationship('Types', back_populates='Kinds_')

class Types(Base):
    __tablename__ = 'Types'

    Type: Mapped[str] = mapped_column(Text, primary_key=True)
    Hash: Mapped[int] = mapped_column(Integer, nullable=False, server_default=text('0'))
    Kind: Mapped[str] = mapped_column(ForeignKey('Kinds.Kind', ondelete='CASCADE', onupdate='CASCADE'), nullable=False)

    Kinds_: Mapped['Kinds'] = relationship('Kinds', back_populates='Types')
    Ages_: Mapped[list['Ages']] = relationship('Ages', secondary='Types_ValidAges', back_populates='Types')
    DiplomacyActions: Mapped[list['DiplomacyActions']] = relationship('DiplomacyActions', foreign_keys='[DiplomacyActions.DiplomacyActionTag]', back_populates='Types_')
    DiplomacyActions_: Mapped[list['DiplomacyActions']] = relationship('DiplomacyActions', secondary='DiplomaticActionValidTokens', back_populates='Types1')
    DiplomacyFavorsGrievancesEventsData: Mapped[list['DiplomacyFavorsGrievancesEventsData']] = relationship('DiplomacyFavorsGrievancesEventsData', back_populates='Types_')
    DynamicModifiers: Mapped[list['DynamicModifiers']] = relationship('DynamicModifiers', foreign_keys='[DynamicModifiers.CollectionType]', back_populates='Types_')
    DynamicModifiers_: Mapped[list['DynamicModifiers']] = relationship('DynamicModifiers', foreign_keys='[DynamicModifiers.EffectType]', back_populates='Types1')
    TypeProperties: Mapped[list['TypeProperties']] = relationship('TypeProperties', back_populates='Types_')
    TypeTags: Mapped[list['TypeTags']] = relationship('TypeTags', back_populates='Types_')
    DiplomaticActionResponseModifiers: Mapped[list['DiplomaticActionResponseModifiers']] = relationship('DiplomaticActionResponseModifiers', back_populates='Types_')
    DiplomaticActionResponses: Mapped[list['DiplomaticActionResponses']] = relationship('DiplomaticActionResponses', back_populates='Types_')
    DiplomaticProjects_UI_Data: Mapped[list['DiplomaticProjectsUIData']] = relationship('DiplomaticProjectsUIData', back_populates='Types_')


class AdvancedStartBuildings(Base):
    __tablename__ = 'AdvancedStartBuildings'

    ConstructibleType: Mapped[str] = mapped_column(Text, primary_key=True)
    TownID: Mapped[int] = mapped_column(Integer, primary_key=True)
    MinimumAdjacency: Mapped[int] = mapped_column(Integer, nullable=False)
    Placement: Mapped[str] = mapped_column(Text, nullable=False)


class AdvancedStartDecks(Base):
    __tablename__ = 'AdvancedStartDecks'

    DeckID: Mapped[str] = mapped_column(Text, primary_key=True)

    AdvancedStartCards: Mapped[list['AdvancedStartCards']] = relationship('AdvancedStartCards', secondary='AdvancedStartDeckCardEntries', back_populates='AdvancedStartDecks_')


class Advisors(Base):
    __tablename__ = 'Advisors'

    AdvisorType: Mapped[str] = mapped_column(Text, primary_key=True)
    Name: Mapped[str] = mapped_column(Text, nullable=False)
    Description: Mapped[Optional[str]] = mapped_column(Text)

    AdvisorSubjects: Mapped[list['AdvisorSubjects']] = relationship('AdvisorSubjects', back_populates='Advisors_')


class AdvisoryClasses(Base):
    __tablename__ = 'AdvisoryClasses'

    AdvisoryClassType: Mapped[str] = mapped_column(Text, primary_key=True)
    Description: Mapped[Optional[str]] = mapped_column(Text)
    Name: Mapped[Optional[str]] = mapped_column(Text)

    ProgressionTreeNodes: Mapped[list['ProgressionTreeNodes']] = relationship('ProgressionTreeNodes', secondary='ProgressionTree_Advisories', back_populates='AdvisoryClasses_')
    Constructibles: Mapped[list['Constructibles']] = relationship('Constructibles', secondary='Constructible_Advisories', back_populates='AdvisoryClasses_')
    Units: Mapped[list['Units']] = relationship('Units', secondary='Unit_Advisories', back_populates='AdvisoryClasses_')
    AdvisorSubjects: Mapped[list['AdvisorSubjects']] = relationship('AdvisorSubjects', back_populates='AdvisoryClasses_')


class AdvisorySubjects(Base):
    __tablename__ = 'AdvisorySubjects'

    AdvisorySubjectType: Mapped[str] = mapped_column(Text, primary_key=True)
    Description: Mapped[Optional[str]] = mapped_column(Text)
    Name: Mapped[Optional[str]] = mapped_column(Text)

    AdvisorSubjects: Mapped[list['AdvisorSubjects']] = relationship('AdvisorSubjects', back_populates='AdvisorySubjects_')


class Affinities(Base):
    __tablename__ = 'Affinities'

    Affinity: Mapped[str] = mapped_column(Text, primary_key=True)
    HostilityChance: Mapped[int] = mapped_column(Integer, nullable=False, server_default=text('100'))
    NeutralityChance: Mapped[int] = mapped_column(Integer, nullable=False, server_default=text('50'))

    Independents: Mapped[list['Independents']] = relationship('Independents', back_populates='Affinities_')


class AgeProgressionRewards(Base):
    __tablename__ = 'AgeProgressionRewards'

    AgeProgressionRewardType: Mapped[str] = mapped_column(Text, primary_key=True)
    ModifierId: Mapped[str] = mapped_column(Text, nullable=False)
    Description: Mapped[Optional[str]] = mapped_column(Text)
    DescriptionFinalAge: Mapped[Optional[str]] = mapped_column(Text)
    Icon: Mapped[Optional[str]] = mapped_column(Text)
    Name: Mapped[Optional[str]] = mapped_column(Text)

    AgeProgressionMilestoneRewards: Mapped[list['AgeProgressionMilestoneRewards']] = relationship('AgeProgressionMilestoneRewards', back_populates='AgeProgressionRewards_')


class AgeProgressions(Base):
    __tablename__ = 'AgeProgressions'

    AgeProgressionType: Mapped[str] = mapped_column(Text, primary_key=True)
    AgeType: Mapped[str] = mapped_column(Text, nullable=False)
    EndsAge: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=text('1'))
    MaxPoints_Abbreviated: Mapped[int] = mapped_column(Integer, nullable=False, server_default=text('0'))
    MaxPoints_Long: Mapped[int] = mapped_column(Integer, nullable=False, server_default=text('0'))
    MaxPoints_Standard: Mapped[int] = mapped_column(Integer, nullable=False, server_default=text('0'))

    AgeCrises: Mapped[list['AgeCrises']] = relationship('AgeCrises', back_populates='AgeProgressions_')
    AgeProgressionEvents: Mapped[list['AgeProgressionEvents']] = relationship('AgeProgressionEvents', back_populates='AgeProgressions_')
    AgeProgressionTurns: Mapped[list['AgeProgressionTurns']] = relationship('AgeProgressionTurns', back_populates='AgeProgressions_')


t_AgeTransitionArmyUnits = Table(
    'AgeTransitionArmyUnits', Base.metadata,
    Column('Age', Text, nullable=False),
    Column('ArmyID', Integer, nullable=False),
    Column('Unit', Text, nullable=False)
)


t_AgeTransitionRespawnModifiers = Table(
    'AgeTransitionRespawnModifiers', Base.metadata,
    Column('ModifierID', Text, nullable=False),
    Column('RespawnType', Text, nullable=False)
)


t_AgeTransitionRespawnParameters = Table(
    'AgeTransitionRespawnParameters', Base.metadata,
    Column('ModifierID', Text, nullable=False),
    Column('RespawnType', Text, nullable=False)
)


t_AgeTransitionRespawnUnits = Table(
    'AgeTransitionRespawnUnits', Base.metadata,
    Column('ArmyID', Integer),
    Column('IsNavy', Boolean, nullable=False, server_default=text('0')),
    Column('RespawnType', Text, nullable=False),
    Column('Unit', Text, nullable=False)
)


class Ages(Base):
    __tablename__ = 'Ages'

    AgeType: Mapped[str] = mapped_column(ForeignKey('Types.Type', ondelete='CASCADE', onupdate='CASCADE'), primary_key=True)
    AgeTechBackgroundTextureOffsetX: Mapped[int] = mapped_column(Integer, nullable=False, server_default=text('0'))
    ChronologyIndex: Mapped[int] = mapped_column(Integer, nullable=False)
    EmbarkedUnitStrength: Mapped[int] = mapped_column(Integer, nullable=False)
    GenerateDiscoveries: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=text('0'))
    GreatPersonBaseCost: Mapped[int] = mapped_column(Integer, nullable=False, server_default=text('0'))
    HumanPlayersPrimaryHemisphere: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=text('0'))
    Name: Mapped[str] = mapped_column(Text, nullable=False)
    NoVictoriesSecondaryHemisphere: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=text('0'))
    NumDefenders: Mapped[int] = mapped_column(Integer, nullable=False, server_default=text('0'))
    SettlementCountOnTransition: Mapped[int] = mapped_column(Integer, nullable=False)
    StartingTraditionSlots: Mapped[int] = mapped_column(Integer, nullable=False)
    AgeTechBackgroundTexture: Mapped[Optional[str]] = mapped_column(Text)
    Description: Mapped[Optional[str]] = mapped_column(Text)
    MainCultureProgressionTreeType: Mapped[Optional[str]] = mapped_column(ForeignKey('ProgressionTrees.ProgressionTreeType', ondelete='CASCADE', onupdate='CASCADE'))
    MainTechProgressionTreeType: Mapped[Optional[str]] = mapped_column(ForeignKey('ProgressionTrees.ProgressionTreeType', ondelete='CASCADE', onupdate='CASCADE'))
    TechTreeLayoutMethod: Mapped[Optional[int]] = mapped_column(Integer)
    TradeSystemParameterSet: Mapped[Optional[str]] = mapped_column(ForeignKey('TradeSystemParameterSets.Type', ondelete='CASCADE', onupdate='CASCADE'))

    ProgressionTrees: Mapped[Optional['ProgressionTrees']] = relationship('ProgressionTrees', foreign_keys=[MainCultureProgressionTreeType], back_populates='Ages_')
    ProgressionTrees_: Mapped[Optional['ProgressionTrees']] = relationship('ProgressionTrees', foreign_keys=[MainTechProgressionTreeType], back_populates='Ages1')
    TradeSystemParameterSets: Mapped[Optional['TradeSystemParameterSets']] = relationship('TradeSystemParameterSets', back_populates='Ages_')
    Governments: Mapped[list['Governments']] = relationship('Governments', secondary='StartingGovernments', back_populates='Ages_')
    ProgressionTrees1: Mapped[list['ProgressionTrees']] = relationship('ProgressionTrees', foreign_keys='[ProgressionTrees.AgeType]', back_populates='Ages2')
    AdvancedStartCardEffects: Mapped[list['AdvancedStartCardEffects']] = relationship('AdvancedStartCardEffects', back_populates='Ages_')
    AdvancedStartCardSets: Mapped[list['AdvancedStartCardSets']] = relationship('AdvancedStartCardSets', back_populates='Ages_')
    AdvancedStartCards: Mapped[list['AdvancedStartCards']] = relationship('AdvancedStartCards', back_populates='Ages_')
    AdvancedStartTowns: Mapped[list['AdvancedStartTowns']] = relationship('AdvancedStartTowns', back_populates='Ages_')
    AgeTransitionBoostableNodes: Mapped[list['AgeTransitionBoostableNodes']] = relationship('AgeTransitionBoostableNodes', back_populates='Ages_')
    AgeTransitionCardSets: Mapped[list['AgeTransitionCardSets']] = relationship('AgeTransitionCardSets', back_populates='Ages_')
    AgeTransitionParameters: Mapped[list['AgeTransitionParameters']] = relationship('AgeTransitionParameters', back_populates='Ages_')
    DiscoveryStory_Yield_Rewards: Mapped[list['DiscoveryStoryYieldRewards']] = relationship('DiscoveryStoryYieldRewards', back_populates='Ages_')
    GameModifiers: Mapped[list['GameModifiers']] = relationship('GameModifiers', back_populates='Ages_')
    GameSpeed_Turns: Mapped[list['GameSpeedTurns']] = relationship('GameSpeedTurns', back_populates='Ages_')
    LegacyPaths: Mapped[list['LegacyPaths']] = relationship('LegacyPaths', back_populates='Ages_')
    MapIslandBehavior: Mapped[list['MapIslandBehavior']] = relationship('MapIslandBehavior', back_populates='Ages_')
    NarrativeStory_Yield_Rewards: Mapped[list['NarrativeStoryYieldRewards']] = relationship('NarrativeStoryYieldRewards', back_populates='Ages_')
    Types: Mapped[list['Types']] = relationship('Types', secondary='Types_ValidAges', back_populates='Ages_')
    AgeCrisisEvents: Mapped[list['AgeCrisisEvents']] = relationship('AgeCrisisEvents', back_populates='Ages_')
    LegacyCivilizations: Mapped[list['LegacyCivilizations']] = relationship('LegacyCivilizations', back_populates='Ages_')
    Constructibles: Mapped[list['Constructibles']] = relationship('Constructibles', back_populates='Ages_')
    Legacies: Mapped[list['Legacies']] = relationship('Legacies', back_populates='Ages_')
    Traditions: Mapped[list['Traditions']] = relationship('Traditions', back_populates='Ages_')
    Resource_ValidAges: Mapped[list['ResourceValidAges']] = relationship('ResourceValidAges', back_populates='Ages_')
    Routes: Mapped[list['Routes']] = relationship('Routes', back_populates='Ages_')
    AdvancedStartUnits: Mapped[list['AdvancedStartUnits']] = relationship('AdvancedStartUnits', back_populates='Ages_')
    BonusMinorStartingUnits: Mapped[list['BonusMinorStartingUnits']] = relationship('BonusMinorStartingUnits', back_populates='Ages_')
    GreatPersonIndividuals: Mapped[list['GreatPersonIndividuals']] = relationship('GreatPersonIndividuals', back_populates='Ages_')
    GreatWorks: Mapped[list['GreatWorks']] = relationship('GreatWorks', back_populates='Ages_')


class AiBudgets(Base):
    __tablename__ = 'AiBudgets'

    Budget: Mapped[str] = mapped_column(Text, primary_key=True)


class AiEvents(Base):
    __tablename__ = 'AiEvents'

    EventType: Mapped[str] = mapped_column(Text, primary_key=True)

    TriggeredBehaviorTrees: Mapped[list['TriggeredBehaviorTrees']] = relationship('TriggeredBehaviorTrees', back_populates='AiEvents_')


class AiListTypes(Base):
    __tablename__ = 'AiListTypes'

    ListType: Mapped[Optional[str]] = mapped_column(Text, primary_key=True)

    Strategies: Mapped[list['Strategies']] = relationship('Strategies', secondary='Strategy_Priorities', back_populates='AiListTypes_')
    AiFavoredItems: Mapped[list['AiFavoredItems']] = relationship('AiFavoredItems', back_populates='AiListTypes_')
    AiLists: Mapped[list['AiLists']] = relationship('AiLists', back_populates='AiListTypes_')
    Beliefs: Mapped[list['Beliefs']] = relationship('Beliefs', secondary='Belief_Priorities', back_populates='AiListTypes_')


class AiOperationLists(Base):
    __tablename__ = 'AiOperationLists'

    ListType: Mapped[str] = mapped_column(Text, primary_key=True)
    BaseList: Mapped[Optional[str]] = mapped_column(ForeignKey('AiOperationLists.ListType', ondelete='CASCADE', onupdate='CASCADE'))

    AiOperationLists: Mapped[Optional['AiOperationLists']] = relationship('AiOperationLists', remote_side=[ListType], back_populates='AiOperationLists_reverse')
    AiOperationLists_reverse: Mapped[list['AiOperationLists']] = relationship('AiOperationLists', remote_side=[BaseList], back_populates='AiOperationLists')
    AiOperationLimits: Mapped[list['AiOperationLimits']] = relationship('AiOperationLimits', back_populates='AiOperationLists_')
    AllowedOperations: Mapped[list['AllowedOperations']] = relationship('AllowedOperations', back_populates='AiOperationLists_')
    Leaders: Mapped[list['Leaders']] = relationship('Leaders', back_populates='AiOperationLists_')


class AiOperationTypes(Base):
    __tablename__ = 'AiOperationTypes'

    OperationType: Mapped[str] = mapped_column(Text, primary_key=True)

    AiOperationDefs: Mapped[list['AiOperationDefs']] = relationship('AiOperationDefs', back_populates='AiOperationTypes_')
    AiOperationLimits: Mapped[list['AiOperationLimits']] = relationship('AiOperationLimits', back_populates='AiOperationTypes_')


class AiPriorities(Base):
    __tablename__ = 'AiPriorities'

    Priority: Mapped[str] = mapped_column(Text, primary_key=True)
    Value: Mapped[float] = mapped_column(REAL, nullable=False)

    AiComponents: Mapped[list['AiComponents']] = relationship('AiComponents', back_populates='AiPriorities_')
    AiTactics: Mapped[list['AiTactics']] = relationship('AiTactics', back_populates='AiPriorities_')
    AiDefinitions: Mapped[list['AiDefinitions']] = relationship('AiDefinitions', back_populates='AiPriorities_')


class AiScoutUses(Base):
    __tablename__ = 'AiScoutUses'

    ScoutUseType: Mapped[str] = mapped_column(Text, primary_key=True)


class AiTeams(Base):
    __tablename__ = 'AiTeams'

    TeamName: Mapped[Optional[str]] = mapped_column(Text, primary_key=True)

    AiOperationTeams: Mapped[list['AiOperationTeams']] = relationship('AiOperationTeams', back_populates='AiTeams_')
    OpTeamRequirements: Mapped[list['OpTeamRequirements']] = relationship('OpTeamRequirements', back_populates='AiTeams_')


class BehaviorTrees(Base):
    __tablename__ = 'BehaviorTrees'

    TreeName: Mapped[str] = mapped_column(Text, primary_key=True)

    AiOperationDefs: Mapped[list['AiOperationDefs']] = relationship('AiOperationDefs', back_populates='BehaviorTrees_')
    TreeData: Mapped[list['TreeData']] = relationship('TreeData', back_populates='BehaviorTrees_')
    TriggeredBehaviorTrees: Mapped[list['TriggeredBehaviorTrees']] = relationship('TriggeredBehaviorTrees', back_populates='BehaviorTrees_')
    BehaviorTreeNodes: Mapped[list['BehaviorTreeNodes']] = relationship('BehaviorTreeNodes', back_populates='BehaviorTrees_')
    BoostHandlers: Mapped[list['BoostHandlers']] = relationship('BoostHandlers', back_populates='BehaviorTrees_')
    Strategies: Mapped[list['Strategies']] = relationship('Strategies', back_populates='BehaviorTrees_')


class BeliefClasses(Base):
    __tablename__ = 'BeliefClasses'

    BeliefClassType: Mapped[str] = mapped_column(Text, primary_key=True)
    AdoptionOrder: Mapped[int] = mapped_column(Integer, nullable=False, server_default=text('1'))
    MaxInReligion: Mapped[int] = mapped_column(Integer, nullable=False, server_default=text('1'))
    Name: Mapped[str] = mapped_column(Text, nullable=False)

    Beliefs: Mapped[list['Beliefs']] = relationship('Beliefs', back_populates='BeliefClasses_')


class Biomes(Base):
    __tablename__ = 'Biomes'

    BiomeType: Mapped[str] = mapped_column(Text, primary_key=True)
    Name: Mapped[str] = mapped_column(Text, nullable=False)
    Description: Mapped[Optional[str]] = mapped_column(Text)
    MaxLatitude: Mapped[Optional[int]] = mapped_column(Integer)

    Terrains: Mapped[list['Terrains']] = relationship('Terrains', secondary='Biome_ValidTerrains', back_populates='Biomes_')
    Constructibles: Mapped[list['Constructibles']] = relationship('Constructibles', secondary='Constructible_InvalidAdjacentBiomes', back_populates='Biomes_')
    Constructibles_: Mapped[list['Constructibles']] = relationship('Constructibles', secondary='Constructible_ValidBiomes', back_populates='Biomes1')
    StartBiasBiomes: Mapped[list['StartBiasBiomes']] = relationship('StartBiasBiomes', back_populates='Biomes_')
    Adjacency_YieldChanges: Mapped[list['AdjacencyYieldChanges']] = relationship('AdjacencyYieldChanges', back_populates='Biomes_')
    Feature_ValidBiomes: Mapped[list['FeatureValidBiomes']] = relationship('FeatureValidBiomes', foreign_keys='[FeatureValidBiomes.BiomeType]', back_populates='Biomes_')
    Feature_ValidBiomes_: Mapped[list['FeatureValidBiomes']] = relationship('FeatureValidBiomes', foreign_keys='[FeatureValidBiomes.ReplaceWithBiomeType]', back_populates='Biomes1')
    RandomEvents: Mapped[list['RandomEvents']] = relationship('RandomEvents', back_populates='Biomes_')
    Resource_ValidBiomes: Mapped[list['ResourceValidBiomes']] = relationship('ResourceValidBiomes', back_populates='Biomes_')
    TerrainBiomeFeature_YieldChanges: Mapped[list['TerrainBiomeFeatureYieldChanges']] = relationship('TerrainBiomeFeatureYieldChanges', back_populates='Biomes_')
    Warehouse_YieldChanges: Mapped[list['WarehouseYieldChanges']] = relationship('WarehouseYieldChanges', back_populates='Biomes_')
    Independents: Mapped[list['Independents']] = relationship('Independents', back_populates='Biomes_')
    GreatPersonIndividuals: Mapped[list['GreatPersonIndividuals']] = relationship('GreatPersonIndividuals', back_populates='Biomes_')


class BoostNames(Base):
    __tablename__ = 'BoostNames'

    BoostType: Mapped[str] = mapped_column(Text, primary_key=True)
    BoostValue: Mapped[int] = mapped_column(Integer, nullable=False)

    Boosts: Mapped[list['Boosts']] = relationship('Boosts', back_populates='BoostNames_')


class Calendars(Base):
    __tablename__ = 'Calendars'

    CalendarType: Mapped[str] = mapped_column(Text, primary_key=True)
    Description: Mapped[Optional[str]] = mapped_column(Text)


class CityEvents(Base):
    __tablename__ = 'CityEvents'

    EventType: Mapped[str] = mapped_column(Text, primary_key=True)


class CityExpansionTypes(Base):
    __tablename__ = 'CityExpansionTypes'

    CityExpansionType: Mapped[str] = mapped_column(Text, primary_key=True)
    Name: Mapped[str] = mapped_column(Text, nullable=False)

    Terrains: Mapped[list['Terrains']] = relationship('Terrains', secondary='CityExpansionValidTerrains', back_populates='CityExpansionTypes_')


class CityStateTypes(Base):
    __tablename__ = 'CityStateTypes'

    CityStateType: Mapped[str] = mapped_column(Text, primary_key=True)
    DisperseRewardAmount: Mapped[int] = mapped_column(Integer, nullable=False, server_default=text('100'))
    Name: Mapped[str] = mapped_column(Text, nullable=False)
    Weight: Mapped[int] = mapped_column(Integer, nullable=False, server_default=text('100'))
    YieldType: Mapped[str] = mapped_column(Text, nullable=False, server_default=text('"NO_YIELD"'))

    CityStateBonuses: Mapped[list['CityStateBonuses']] = relationship('CityStateBonuses', back_populates='CityStateTypes_')
    Independents: Mapped[list['Independents']] = relationship('Independents', back_populates='CityStateTypes_')


class CivilizationLevels(Base):
    __tablename__ = 'CivilizationLevels'

    CivilizationLevelType: Mapped[str] = mapped_column(Text, primary_key=True)
    CanBuildWonders: Mapped[bool] = mapped_column(Boolean, nullable=False)
    CanEarnGreatPeople: Mapped[bool] = mapped_column(Boolean, nullable=False)
    CanFoundCities: Mapped[bool] = mapped_column(Boolean, nullable=False)
    CanGiveInfluence: Mapped[bool] = mapped_column(Boolean, nullable=False)
    CanReceiveInfluence: Mapped[bool] = mapped_column(Boolean, nullable=False)
    IgnoresUnitStrategicResourceRequirements: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=text('0'))

    Civilizations: Mapped[list['Civilizations']] = relationship('Civilizations', back_populates='CivilizationLevels_')
    UnitDiplomacyAction_Targets: Mapped[list['UnitDiplomacyActionTargets']] = relationship('UnitDiplomacyActionTargets', back_populates='CivilizationLevels_')


class CivilopediaPageChapterHeaders(Base):
    __tablename__ = 'CivilopediaPageChapterHeaders'

    ChapterID: Mapped[str] = mapped_column(Text, primary_key=True)
    PageID: Mapped[str] = mapped_column(Text, primary_key=True)
    SectionID: Mapped[str] = mapped_column(Text, primary_key=True)
    Header: Mapped[str] = mapped_column(Text, nullable=False)


class CivilopediaPageChapterParagraphs(Base):
    __tablename__ = 'CivilopediaPageChapterParagraphs'

    ChapterID: Mapped[str] = mapped_column(Text, primary_key=True)
    PageID: Mapped[str] = mapped_column(Text, primary_key=True)
    SectionID: Mapped[str] = mapped_column(Text, primary_key=True)
    Paragraph: Mapped[str] = mapped_column(Text, nullable=False)
    SortIndex: Mapped[int] = mapped_column(Integer, nullable=False, server_default=text('0'))


class CivilopediaPageExcludes(Base):
    __tablename__ = 'CivilopediaPageExcludes'

    PageID: Mapped[str] = mapped_column(Text, primary_key=True)
    SectionID: Mapped[str] = mapped_column(Text, primary_key=True)


class CivilopediaPageGroupExcludes(Base):
    __tablename__ = 'CivilopediaPageGroupExcludes'

    PageGroupID: Mapped[str] = mapped_column(Text, primary_key=True)
    SectionID: Mapped[str] = mapped_column(Text, primary_key=True)


t_CivilopediaPageGroupQueries = Table(
    'CivilopediaPageGroupQueries', Base.metadata,
    Column('SectionID', Text, nullable=False),
    Column('SQL', Text, nullable=False)
)


class CivilopediaPageGroups(Base):
    __tablename__ = 'CivilopediaPageGroups'

    PageGroupID: Mapped[str] = mapped_column(Text, primary_key=True)
    SectionID: Mapped[str] = mapped_column(Text, primary_key=True)
    Name: Mapped[str] = mapped_column(Text, nullable=False)
    SortIndex: Mapped[int] = mapped_column(Integer, nullable=False, server_default=text('0'))
    VisibleIfEmpty: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=text('0'))


class CivilopediaPageLayoutChapterContentQueries(Base):
    __tablename__ = 'CivilopediaPageLayoutChapterContentQueries'

    ChapterID: Mapped[str] = mapped_column(Text, primary_key=True)
    PageLayoutID: Mapped[str] = mapped_column(Text, primary_key=True)
    SQL: Mapped[str] = mapped_column(Text, nullable=False)


class CivilopediaPageLayouts(Base):
    __tablename__ = 'CivilopediaPageLayouts'

    PageLayoutID: Mapped[str] = mapped_column(Text, primary_key=True)
    UseSidebar: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=text('1'))

    CivilopediaPageLayoutChapters: Mapped[list['CivilopediaPageLayoutChapters']] = relationship('CivilopediaPageLayoutChapters', back_populates='CivilopediaPageLayouts_')
    CivilopediaPages: Mapped[list['CivilopediaPages']] = relationship('CivilopediaPages', back_populates='CivilopediaPageLayouts_')


t_CivilopediaPageQueries = Table(
    'CivilopediaPageQueries', Base.metadata,
    Column('SectionID', Text, nullable=False),
    Column('SQL', Text, nullable=False)
)


t_CivilopediaPageSearchTermQueries = Table(
    'CivilopediaPageSearchTermQueries', Base.metadata,
    Column('SQL', Text, nullable=False)
)


class CivilopediaPageSearchTerms(Base):
    __tablename__ = 'CivilopediaPageSearchTerms'

    PageID: Mapped[str] = mapped_column(Text, primary_key=True)
    SectionID: Mapped[str] = mapped_column(Text, primary_key=True)
    Term: Mapped[str] = mapped_column(Text, primary_key=True)


t_CivilopediaPageSidebarPanels = Table(
    'CivilopediaPageSidebarPanels', Base.metadata,
    Column('Component', Text, nullable=False),
    Column('PageID', Text),
    Column('SectionID', Text),
    Column('SortIndex', Integer, nullable=False, server_default=text('100'))
)


class CivilopediaSectionExcludes(Base):
    __tablename__ = 'CivilopediaSectionExcludes'

    SectionID: Mapped[str] = mapped_column(Text, primary_key=True)


class CivilopediaSections(Base):
    __tablename__ = 'CivilopediaSections'

    SectionID: Mapped[str] = mapped_column(Text, primary_key=True)
    Name: Mapped[str] = mapped_column(Text, nullable=False)
    SortIndex: Mapped[int] = mapped_column(Integer, nullable=False, server_default=text('0'))
    Icon: Mapped[Optional[str]] = mapped_column(Text)


class ConstructibleClasses(Base):
    __tablename__ = 'ConstructibleClasses'

    ConstructibleClassType: Mapped[str] = mapped_column(Text, primary_key=True)
    Name: Mapped[str] = mapped_column(Text, nullable=False)
    Description: Mapped[Optional[str]] = mapped_column(Text)


class ConstructibleModifiers(Base):
    __tablename__ = 'ConstructibleModifiers'

    ConstructibleType: Mapped[str] = mapped_column(Text, primary_key=True)
    ModifierId: Mapped[str] = mapped_column(Text, primary_key=True)


class ConstructibleRoleIcons(Base):
    __tablename__ = 'Constructible_RoleIcons'

    ConstructibleType: Mapped[str] = mapped_column(Text, primary_key=True)
    IconPath: Mapped[str] = mapped_column(Text, primary_key=True)
    Context: Mapped[Optional[str]] = mapped_column(Text)


class Continents(Base):
    __tablename__ = 'Continents'

    ContinentType: Mapped[str] = mapped_column(Text, primary_key=True)
    Description: Mapped[Optional[str]] = mapped_column(Text)

    CityNames: Mapped[list['CityNames']] = relationship('CityNames', back_populates='Continents_')


class DataTypes(Base):
    __tablename__ = 'DataTypes'

    DataId: Mapped[int] = mapped_column(Integer, primary_key=True)
    TypeName: Mapped[str] = mapped_column(Text, nullable=False)

    NodeDataDefinitions: Mapped[list['NodeDataDefinitions']] = relationship('NodeDataDefinitions', back_populates='DataTypes_')


class DealItemAgreements(Base):
    __tablename__ = 'DealItemAgreements'

    Type: Mapped[str] = mapped_column(Text, primary_key=True)
    Description: Mapped[str] = mapped_column(Text, nullable=False)
    Name: Mapped[str] = mapped_column(Text, nullable=False)


class DealItems(Base):
    __tablename__ = 'DealItems'

    Type: Mapped[str] = mapped_column(Text, primary_key=True)
    Description: Mapped[str] = mapped_column(Text, nullable=False)
    Name: Mapped[str] = mapped_column(Text, nullable=False)


class Difficulties(Base):
    __tablename__ = 'Difficulties'

    DifficultyType: Mapped[str] = mapped_column(Text, primary_key=True)
    Name: Mapped[str] = mapped_column(Text, nullable=False)

    AdvisorWarnings: Mapped[list['AdvisorWarnings']] = relationship('AdvisorWarnings', back_populates='Difficulties_')
    AiFavoredItems: Mapped[list['AiFavoredItems']] = relationship('AiFavoredItems', foreign_keys='[AiFavoredItems.MaxDifficulty]', back_populates='Difficulties_')
    AiFavoredItems_: Mapped[list['AiFavoredItems']] = relationship('AiFavoredItems', foreign_keys='[AiFavoredItems.MinDifficulty]', back_populates='Difficulties1')
    AiLists: Mapped[list['AiLists']] = relationship('AiLists', foreign_keys='[AiLists.MaxDifficulty]', back_populates='Difficulties_')
    AiLists_: Mapped[list['AiLists']] = relationship('AiLists', foreign_keys='[AiLists.MinDifficulty]', back_populates='Difficulties1')
    BarbarianAttackForces: Mapped[list['BarbarianAttackForces']] = relationship('BarbarianAttackForces', foreign_keys='[BarbarianAttackForces.MaxTargetDifficulty]', back_populates='Difficulties_')
    BarbarianAttackForces_: Mapped[list['BarbarianAttackForces']] = relationship('BarbarianAttackForces', foreign_keys='[BarbarianAttackForces.MinTargetDifficulty]', back_populates='Difficulties1')
    StandardHandicaps: Mapped[list['StandardHandicaps']] = relationship('StandardHandicaps', back_populates='Difficulties_')
    AdvancedStartUnits: Mapped[list['AdvancedStartUnits']] = relationship('AdvancedStartUnits', back_populates='Difficulties_')
    BonusMinorStartingUnits: Mapped[list['BonusMinorStartingUnits']] = relationship('BonusMinorStartingUnits', back_populates='Difficulties_')


class DiplomacyPlayerRelationships(Base):
    __tablename__ = 'DiplomacyPlayerRelationships'

    DiplomacyPlayerRelationshipType: Mapped[str] = mapped_column(Text, primary_key=True)
    MaxRelationship: Mapped[int] = mapped_column(Integer, nullable=False, server_default=text('-999'))
    MinRelationship: Mapped[int] = mapped_column(Integer, nullable=False, server_default=text('-999'))
    Name: Mapped[str] = mapped_column(Text, nullable=False)


class DiplomacyStatementFrames(Base):
    __tablename__ = 'DiplomacyStatementFrames'

    Frame: Mapped[str] = mapped_column(Text, primary_key=True)
    Initiator: Mapped[str] = mapped_column(Text, primary_key=True)
    Type: Mapped[str] = mapped_column(Text, primary_key=True)
    Selections: Mapped[Optional[str]] = mapped_column(Text)
    Text_: Mapped[Optional[str]] = mapped_column('Text', Text)


class DiplomacyStatementSelections(Base):
    __tablename__ = 'DiplomacyStatementSelections'

    Sort: Mapped[float] = mapped_column(REAL, primary_key=True)
    Type: Mapped[str] = mapped_column(Text, primary_key=True)
    Key: Mapped[str] = mapped_column(Text, nullable=False)
    Text_: Mapped[str] = mapped_column('Text', Text, nullable=False)


class DiplomacyStatements(Base):
    __tablename__ = 'DiplomacyStatements'

    DiplomacyStatementType: Mapped[str] = mapped_column(Text, primary_key=True)
    GroupType: Mapped[str] = mapped_column(Text, nullable=False)
    AutoActivate: Mapped[Optional[str]] = mapped_column(Text)


class DiscoveryStoryActivations(Base):
    __tablename__ = 'DiscoveryStory_Activations'

    Type: Mapped[str] = mapped_column(Text, primary_key=True)

    DiscoverySiftingImprovements: Mapped[list['DiscoverySiftingImprovements']] = relationship('DiscoverySiftingImprovements', back_populates='DiscoveryStory_Activations')


class DisplayQueuePriorities(Base):
    __tablename__ = 'DisplayQueuePriorities'

    Category: Mapped[str] = mapped_column(Text, primary_key=True)
    Priority: Mapped[int] = mapped_column(Integer, nullable=False, server_default=text('0'))


class EventPopupData(Base):
    __tablename__ = 'EventPopupData'

    Type: Mapped[str] = mapped_column(Text, primary_key=True)
    Title: Mapped[str] = mapped_column(Text, nullable=False)
    BackgroundImage: Mapped[Optional[str]] = mapped_column(Text)
    Description: Mapped[Optional[str]] = mapped_column(Text)
    Effects: Mapped[Optional[str]] = mapped_column(Text)
    EffectType: Mapped[Optional[str]] = mapped_column(Text)
    FilterCondition: Mapped[Optional[str]] = mapped_column(Text)
    ForegroundImage: Mapped[Optional[str]] = mapped_column(Text)
    ImageText: Mapped[Optional[str]] = mapped_column(Text)


class Fertilities(Base):
    __tablename__ = 'Fertilities'

    FertilityType: Mapped[str] = mapped_column(Text, primary_key=True)
    Name: Mapped[str] = mapped_column(Text, nullable=False)
    Description: Mapped[Optional[str]] = mapped_column(Text)


class GameCoreEvents(Base):
    __tablename__ = 'GameCoreEvents'

    Name: Mapped[str] = mapped_column(Text, primary_key=True)


class GameSpeeds(Base):
    __tablename__ = 'GameSpeeds'

    GameSpeedType: Mapped[str] = mapped_column(Text, primary_key=True)
    CostMultiplier: Mapped[int] = mapped_column(Integer, nullable=False, server_default=text('100'))
    Name: Mapped[str] = mapped_column(Text, nullable=False)
    Description: Mapped[Optional[str]] = mapped_column(Text)

    GameSpeed_Scalings: Mapped[list['GameSpeedScalings']] = relationship('GameSpeedScalings', back_populates='GameSpeeds_')
    GameSpeed_Turns: Mapped[list['GameSpeedTurns']] = relationship('GameSpeedTurns', back_populates='GameSpeeds_')


class GlobalParameters(Base):
    __tablename__ = 'GlobalParameters'

    Name: Mapped[str] = mapped_column(Text, primary_key=True)
    Value: Mapped[str] = mapped_column(Text, nullable=False)


class GoldenAges(Base):
    __tablename__ = 'GoldenAges'

    GoldenAgeType: Mapped[str] = mapped_column(Text, primary_key=True)
    Description: Mapped[str] = mapped_column(Text, nullable=False)
    Name: Mapped[str] = mapped_column(Text, nullable=False)

    Governments: Mapped[list['Governments']] = relationship('Governments', secondary='Government_ValidGoldenAges', back_populates='GoldenAges_')
    GoldenAgeModifiers: Mapped[list['GoldenAgeModifiers']] = relationship('GoldenAgeModifiers', back_populates='GoldenAges_')


class GoodyHuts(Base):
    __tablename__ = 'GoodyHuts'

    GoodyHutType: Mapped[str] = mapped_column(Text, primary_key=True)
    Weight: Mapped[int] = mapped_column(Integer, nullable=False)

    GoodyHutSubTypes: Mapped[list['GoodyHutSubTypes']] = relationship('GoodyHutSubTypes', back_populates='GoodyHuts_')


class Governments(Base):
    __tablename__ = 'Governments'

    GovernmentType: Mapped[str] = mapped_column(Text, primary_key=True)
    CelebrationName: Mapped[str] = mapped_column(Text, nullable=False)
    Name: Mapped[str] = mapped_column(Text, nullable=False)
    Description: Mapped[Optional[str]] = mapped_column(Text)

    Ages_: Mapped[list['Ages']] = relationship('Ages', secondary='StartingGovernments', back_populates='Governments')
    GoldenAges_: Mapped[list['GoldenAges']] = relationship('GoldenAges', secondary='Government_ValidGoldenAges', back_populates='Governments')
    Modifiers: Mapped[list['Modifiers']] = relationship('Modifiers', secondary='GovernmentModifiers', back_populates='Governments_')
    Attributes: Mapped[list['Attributes']] = relationship('Attributes', secondary='GovernmentAttributes', back_populates='Governments_')


class GreatPersonIndividualIconModifiers(Base):
    __tablename__ = 'GreatPersonIndividualIconModifiers'

    GreatPersonIndividualType: Mapped[str] = mapped_column(Text, primary_key=True)
    OverrideUnitIcon: Mapped[str] = mapped_column(Text, nullable=False)


class GreatWorkSlotTypes(Base):
    __tablename__ = 'GreatWorkSlotTypes'

    GreatWorkSlotType: Mapped[str] = mapped_column(Text, primary_key=True)

    GreatWorkObjectTypes: Mapped[list['GreatWorkObjectTypes']] = relationship('GreatWorkObjectTypes', secondary='GreatWork_ValidSubTypes', back_populates='GreatWorkSlotTypes_')
    Constructible_GreatWorks: Mapped[list['ConstructibleGreatWorks']] = relationship('ConstructibleGreatWorks', back_populates='GreatWorkSlotTypes_')


class GreatWorkSourceTypes(Base):
    __tablename__ = 'GreatWorkSourceTypes'

    GreatWorkSourceType: Mapped[str] = mapped_column(Text, primary_key=True)

    GreatWorks: Mapped[list['GreatWorks']] = relationship('GreatWorks', back_populates='GreatWorkSourceTypes_')


class HandicapSystems(Base):
    __tablename__ = 'HandicapSystems'

    HandicapSystemType: Mapped[str] = mapped_column(Text, primary_key=True)
    Name: Mapped[str] = mapped_column(Text, nullable=False)
    NumLevels: Mapped[int] = mapped_column(Integer, nullable=False, server_default=text('2'))

    StandardHandicaps: Mapped[list['StandardHandicaps']] = relationship('StandardHandicaps', back_populates='HandicapSystems_')


class HistoricRankings(Base):
    __tablename__ = 'HistoricRankings'

    Score: Mapped[int] = mapped_column(Integer, nullable=False, server_default=text('0'))
    HistoricLeader: Mapped[Optional[str]] = mapped_column(Text, primary_key=True)
    Quote: Mapped[Optional[str]] = mapped_column(Text)


class IProperties(Base):
    __tablename__ = 'IProperties'

    Collection: Mapped[str] = mapped_column(Text, primary_key=True)
    Name: Mapped[str] = mapped_column(Text, primary_key=True)
    Type: Mapped[str] = mapped_column(Text, nullable=False)
    Container: Mapped[Optional[str]] = mapped_column(Text)
    Access: Mapped[Optional[str]] = mapped_column(Text)
    Definition: Mapped[Optional[str]] = mapped_column(Text)
    InitializeBy: Mapped[Optional[str]] = mapped_column(Text)
    Value: Mapped[Optional[str]] = mapped_column(Text)


class IPropertyTypes(Base):
    __tablename__ = 'IPropertyTypes'

    Type: Mapped[str] = mapped_column(Text, primary_key=True)
    KindOf: Mapped[Optional[str]] = mapped_column(Text)
    Definition: Mapped[Optional[str]] = mapped_column(Text)


class InterfaceModes(Base):
    __tablename__ = 'InterfaceModes'

    InterfaceModeType: Mapped[str] = mapped_column(Text, primary_key=True)
    ViewName: Mapped[str] = mapped_column(Text, nullable=False)
    CustomCursor: Mapped[Optional[str]] = mapped_column(Text)

    UnitCommands: Mapped[list['UnitCommands']] = relationship('UnitCommands', back_populates='InterfaceModes_')
    UnitOperations: Mapped[list['UnitOperations']] = relationship('UnitOperations', back_populates='InterfaceModes_')


class KeywordAbilities(Base):
    __tablename__ = 'KeywordAbilities'

    KeywordAbilityType: Mapped[str] = mapped_column(Text, primary_key=True)
    FullDescription: Mapped[str] = mapped_column(Text, nullable=False)
    Name: Mapped[str] = mapped_column(Text, nullable=False)
    Summary: Mapped[str] = mapped_column(Text, nullable=False)
    CivilopediaKey: Mapped[Optional[str]] = mapped_column(Text)
    IconString: Mapped[Optional[str]] = mapped_column(Text)

    UnitAbilities: Mapped[list['UnitAbilities']] = relationship('UnitAbilities', back_populates='KeywordAbilities_')


class LegacyIndependents(Base):
    __tablename__ = 'LegacyIndependents'

    IndependentType: Mapped[str] = mapped_column(Text, primary_key=True)
    Age: Mapped[str] = mapped_column(Text, nullable=False)
    Name: Mapped[str] = mapped_column(Text, nullable=False)


class LegacyPathClasses(Base):
    __tablename__ = 'LegacyPathClasses'

    LegacyPathClassType: Mapped[str] = mapped_column(Text, primary_key=True)
    Name: Mapped[str] = mapped_column(Text, nullable=False)

    LegacyPaths: Mapped[list['LegacyPaths']] = relationship('LegacyPaths', back_populates='LegacyPathClasses_')


class LegacySets(Base):
    __tablename__ = 'LegacySets'

    LegacySetType: Mapped[str] = mapped_column(Text, primary_key=True)
    Name: Mapped[str] = mapped_column(Text, nullable=False)
    Description: Mapped[Optional[str]] = mapped_column(Text)


class MapRainfalls(Base):
    __tablename__ = 'MapRainfalls'

    MapRainfallType: Mapped[str] = mapped_column(Text, primary_key=True)
    AverageAmountPerYear: Mapped[Optional[int]] = mapped_column(Integer)
    Description: Mapped[Optional[str]] = mapped_column(Text)
    Name: Mapped[Optional[str]] = mapped_column(Text)
    Scale: Mapped[Optional[float]] = mapped_column(REAL)


class MapResourceDistributions(Base):
    __tablename__ = 'MapResourceDistributions'

    MapResourceDistributionType: Mapped[str] = mapped_column(Text, primary_key=True)
    Description: Mapped[str] = mapped_column(Text, nullable=False)
    Name: Mapped[str] = mapped_column(Text, nullable=False)
    Scale: Mapped[Optional[float]] = mapped_column(REAL)


class MapResourceMinimumAmountModifier(Base):
    __tablename__ = 'MapResourceMinimumAmountModifier'

    MapSizeType: Mapped[str] = mapped_column(Text, primary_key=True)
    MapType: Mapped[str] = mapped_column(Text, primary_key=True)
    Amount: Mapped[int] = mapped_column(Integer, nullable=False, server_default=text('0'))


class MapSeaLevels(Base):
    __tablename__ = 'MapSeaLevels'

    MapSeaLevelType: Mapped[str] = mapped_column(Text, primary_key=True)
    Description: Mapped[str] = mapped_column(Text, nullable=False)
    Name: Mapped[str] = mapped_column(Text, nullable=False)
    Scale: Mapped[Optional[float]] = mapped_column(REAL)


class MapStartPositions(Base):
    __tablename__ = 'MapStartPositions'

    Map: Mapped[str] = mapped_column(Text, primary_key=True)
    Plot: Mapped[int] = mapped_column(Integer, primary_key=True)
    Type: Mapped[str] = mapped_column(Text, nullable=False)
    Value: Mapped[Optional[str]] = mapped_column(Text)


class MapTemperatures(Base):
    __tablename__ = 'MapTemperatures'

    MapTemperatureType: Mapped[str] = mapped_column(Text, primary_key=True)
    Description: Mapped[str] = mapped_column(Text, nullable=False)
    Name: Mapped[str] = mapped_column(Text, nullable=False)
    AverageStartingTemperature: Mapped[Optional[float]] = mapped_column(REAL)
    Scale: Mapped[Optional[float]] = mapped_column(REAL)


class MapWorldAges(Base):
    __tablename__ = 'MapWorldAges'

    MapWorldAgeType: Mapped[str] = mapped_column(Text, primary_key=True)
    Description: Mapped[str] = mapped_column(Text, nullable=False)
    Name: Mapped[str] = mapped_column(Text, nullable=False)
    Scale: Mapped[Optional[float]] = mapped_column(REAL)
    YearsOld: Mapped[Optional[float]] = mapped_column(REAL)


class Maps(Base):
    __tablename__ = 'Maps'

    MapSizeType: Mapped[str] = mapped_column(Text, primary_key=True)
    AllOnLargestLandmass: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=text('0'))
    Continents_: Mapped[int] = mapped_column('Continents', Integer, nullable=False, server_default=text('1'))
    DefaultPlayers: Mapped[int] = mapped_column(Integer, nullable=False, server_default=text('0'))
    GridHeight: Mapped[int] = mapped_column(Integer, nullable=False, server_default=text('0'))
    GridWidth: Mapped[int] = mapped_column(Integer, nullable=False, server_default=text('0'))
    LakeGenerationFrequency: Mapped[int] = mapped_column(Integer, nullable=False, server_default=text('25'))
    LakeSizeCutoff: Mapped[int] = mapped_column(Integer, nullable=False, server_default=text('0'))
    Name: Mapped[str] = mapped_column(Text, nullable=False)
    NumNaturalWonders: Mapped[int] = mapped_column(Integer, nullable=False, server_default=text('0'))
    OceanWidth: Mapped[int] = mapped_column(Integer, nullable=False, server_default=text('0'))
    PlayersLandmass1: Mapped[int] = mapped_column(Integer, nullable=False, server_default=text('0'))
    PlayersLandmass2: Mapped[int] = mapped_column(Integer, nullable=False, server_default=text('0'))
    StartSectorCols: Mapped[int] = mapped_column(Integer, nullable=False, server_default=text('3'))
    StartSectorRows: Mapped[int] = mapped_column(Integer, nullable=False, server_default=text('3'))
    Description: Mapped[Optional[str]] = mapped_column(Text)

    AgeProgressionEventMapSizeOverrides: Mapped[list['AgeProgressionEventMapSizeOverrides']] = relationship('AgeProgressionEventMapSizeOverrides', back_populates='Maps_')
    Map_GreatPersonClasses: Mapped[list['MapGreatPersonClasses']] = relationship('MapGreatPersonClasses', back_populates='Maps_')


class Mementos(Base):
    __tablename__ = 'Mementos'

    MementoType: Mapped[str] = mapped_column(Text, primary_key=True)
    Description: Mapped[str] = mapped_column(Text, nullable=False)
    FunctionalDescription: Mapped[str] = mapped_column(Text, nullable=False)
    Name: Mapped[str] = mapped_column(Text, nullable=False)
    Region: Mapped[str] = mapped_column(Text, nullable=False)
    Tag: Mapped[str] = mapped_column(Text, nullable=False)
    Tier: Mapped[int] = mapped_column(Integer, nullable=False)

    Modifiers: Mapped[list['Modifiers']] = relationship('Modifiers', secondary='MementoModifiers', back_populates='Mementos_')


class ModifierCategories(Base):
    __tablename__ = 'ModifierCategories'

    ModifierCategoryType: Mapped[str] = mapped_column(Text, primary_key=True)
    Name: Mapped[str] = mapped_column(Text, nullable=False)
    Description: Mapped[Optional[str]] = mapped_column(Text)


class ModifierMetadatas(Base):
    __tablename__ = 'ModifierMetadatas'

    FieldName: Mapped[str] = mapped_column(Text, primary_key=True)
    ModifierID: Mapped[str] = mapped_column(Text, primary_key=True)
    String: Mapped[Optional[str]] = mapped_column(Text)
    Value: Mapped[Optional[float]] = mapped_column(REAL)


class ModifierTokens(Base):
    __tablename__ = 'ModifierTokens'

    RelationshipModifier: Mapped[str] = mapped_column(Text, primary_key=True)
    FavorsGiven: Mapped[int] = mapped_column(Integer, nullable=False, server_default=text('0'))
    GrievancesGiven: Mapped[int] = mapped_column(Integer, nullable=False, server_default=text('0'))
    UseSupportEvent: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=text('0'))


class Months(Base):
    __tablename__ = 'Months'

    MonthType: Mapped[str] = mapped_column(Text, primary_key=True)
    Description: Mapped[str] = mapped_column(Text, nullable=False)


class Movies(Base):
    __tablename__ = 'Movies'

    Locale: Mapped[str] = mapped_column(Text, primary_key=True)
    MovieType: Mapped[str] = mapped_column(Text, primary_key=True)
    Resolution: Mapped[int] = mapped_column(Integer, primary_key=True)
    Url: Mapped[str] = mapped_column(Text, nullable=False)
    UseCoverFitMode: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=text('0'))
    Audio: Mapped[Optional[str]] = mapped_column(Text)
    StopAudio: Mapped[Optional[str]] = mapped_column(Text)
    Subtitles: Mapped[Optional[str]] = mapped_column(Text)


class NamedRivers(Base):
    __tablename__ = 'NamedRivers'

    NamedRiverType: Mapped[str] = mapped_column(Text, primary_key=True)
    Name: Mapped[str] = mapped_column(Text, nullable=False)

    NamedRiverCivilizations: Mapped[list['NamedRiverCivilizations']] = relationship('NamedRiverCivilizations', back_populates='NamedRivers_')


class NamedVolcanoes(Base):
    __tablename__ = 'NamedVolcanoes'

    NamedVolcanoType: Mapped[str] = mapped_column(Text, primary_key=True)
    Name: Mapped[str] = mapped_column(Text, nullable=False)

    NamedVolcanoCivilizations: Mapped[list['NamedVolcanoCivilizations']] = relationship('NamedVolcanoCivilizations', back_populates='NamedVolcanoes_')


class NarrativeRewards(Base):
    __tablename__ = 'NarrativeRewards'

    NarrativeRewardType: Mapped[str] = mapped_column(Text, primary_key=True)
    ModifierID: Mapped[str] = mapped_column(Text, nullable=False)

    NarrativeStory_Rewards: Mapped[list['NarrativeStoryRewards']] = relationship('NarrativeStoryRewards', back_populates='NarrativeRewards_')


class NarrativeStoryActivations(Base):
    __tablename__ = 'NarrativeStory_Activations'

    Type: Mapped[str] = mapped_column(Text, primary_key=True)

    NarrativeStories: Mapped[list['NarrativeStories']] = relationship('NarrativeStories', back_populates='NarrativeStory_Activations')


class NarrativeStoryQueues(Base):
    __tablename__ = 'NarrativeStory_Queues'

    QueueType: Mapped[str] = mapped_column(Text, primary_key=True)
    ActivationCount: Mapped[int] = mapped_column(Integer, nullable=False, server_default=text('0'))
    StartAll: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=text('0'))

    NarrativeStories: Mapped[list['NarrativeStories']] = relationship('NarrativeStories', back_populates='NarrativeStory_Queues')


class NarrativeStoryRewardIcons(Base):
    __tablename__ = 'NarrativeStory_RewardIcons'

    Type: Mapped[str] = mapped_column(Text, primary_key=True)
    AudioName: Mapped[str] = mapped_column(Text, nullable=False)


class NarrativeStoryRewardActivations(Base):
    __tablename__ = 'NarrativeStory_Reward_Activations'

    Type: Mapped[str] = mapped_column(Text, primary_key=True)

    NarrativeStory_Rewards: Mapped[list['NarrativeStoryRewards']] = relationship('NarrativeStoryRewards', back_populates='NarrativeStory_Reward_Activations')


class NarrativeStoryTextReplacementTypes(Base):
    __tablename__ = 'NarrativeStory_TextReplacementTypes'

    Type: Mapped[str] = mapped_column(Text, primary_key=True)


class NarrativeStoryTextTypes(Base):
    __tablename__ = 'NarrativeStory_TextTypes'

    Type: Mapped[str] = mapped_column(Text, primary_key=True)


class NarrativeStoryUIActivations(Base):
    __tablename__ = 'NarrativeStory_UIActivations'

    Type: Mapped[str] = mapped_column(Text, primary_key=True)

    NarrativeStories: Mapped[list['NarrativeStories']] = relationship('NarrativeStories', back_populates='NarrativeStory_UIActivations')


class NarrativeTags(Base):
    __tablename__ = 'NarrativeTags'

    NarrativeTagType: Mapped[str] = mapped_column(Text, primary_key=True)


class NotificationSounds(Base):
    __tablename__ = 'NotificationSounds'

    Context: Mapped[str] = mapped_column(Text, primary_key=True)
    NotificationType: Mapped[str] = mapped_column(Text, primary_key=True)
    Audio: Mapped[Optional[str]] = mapped_column(Text)


class Notifications(Base):
    __tablename__ = 'Notifications'

    NotificationType: Mapped[str] = mapped_column(Text, primary_key=True)
    AutoActivate: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=text('0'))
    AutoNotify: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=text('0'))
    ExpiresEndOfNextTurn: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=text('0'))
    ExpiresEndOfTurn: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=text('1'))
    Priority: Mapped[int] = mapped_column(Integer, nullable=False)
    ShowIconSinglePlayer: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=text('1'))
    VisibleInUI: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=text('1'))
    GroupType: Mapped[Optional[str]] = mapped_column(Text)
    Icon: Mapped[Optional[str]] = mapped_column(Text)
    Message: Mapped[Optional[str]] = mapped_column(Text)
    SeverityType: Mapped[Optional[str]] = mapped_column(Text)
    SubType: Mapped[Optional[str]] = mapped_column(Text)
    Summary: Mapped[Optional[str]] = mapped_column(Text)


class Origins(Base):
    __tablename__ = 'Origins'

    OriginType: Mapped[str] = mapped_column(Text, primary_key=True)
    Name: Mapped[str] = mapped_column(Text, nullable=False)
    Description: Mapped[Optional[str]] = mapped_column(Text)


class PlayerModifiers(Base):
    __tablename__ = 'PlayerModifiers'

    ModifierId: Mapped[str] = mapped_column(Text, primary_key=True)


class PlotEffects(Base):
    __tablename__ = 'PlotEffects'

    PlotEffectType: Mapped[str] = mapped_column(Text, primary_key=True)
    AllowConstructWhileDamaged: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=text('1'))
    AllowOnWater: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=text('1'))
    Damage: Mapped[int] = mapped_column(Integer, nullable=False, server_default=text('0'))
    Defense: Mapped[int] = mapped_column(Integer, nullable=False, server_default=text('0'))
    Name: Mapped[str] = mapped_column(Text, nullable=False)
    OnlyVisibleToOwner: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=text('0'))
    RemoveOnEnter: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=text('0'))
    TimeDecay: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=text('0'))
    TimeValue: Mapped[int] = mapped_column(Integer, nullable=False, server_default=text('0'))
    TriggerOnEnter: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=text('0'))
    UnoccupiedDecay: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=text('0'))

    VisArt_PlotEffectModifiers: Mapped[list['VisArtPlotEffectModifiers']] = relationship('VisArtPlotEffectModifiers', back_populates='PlotEffects_')


class PlotEvalConditions(Base):
    __tablename__ = 'PlotEvalConditions'

    ConditionType: Mapped[str] = mapped_column(Text, primary_key=True)
    GoodValue: Mapped[int] = mapped_column(Integer, nullable=False, server_default=text('0'))
    PoorValue: Mapped[int] = mapped_column(Integer, nullable=False, server_default=text('0'))
    Value: Mapped[int] = mapped_column(Integer, nullable=False)
    GoodTooltipString: Mapped[Optional[str]] = mapped_column(Text)
    PoorTooltipString: Mapped[Optional[str]] = mapped_column(Text)


class Plunders(Base):
    __tablename__ = 'Plunders'

    PlunderType: Mapped[str] = mapped_column(Text, primary_key=True)
    Name: Mapped[str] = mapped_column(Text, nullable=False)

    Constructible_Plunders: Mapped[list['ConstructiblePlunders']] = relationship('ConstructiblePlunders', back_populates='Plunders_')


t_PrevailingWinds = Table(
    'PrevailingWinds', Base.metadata,
    Column('DirectionType', Text, nullable=False),
    Column('MaximumLatitude', Integer, nullable=False),
    Column('MinimumLatitude', Integer, nullable=False),
    Column('Weight', Integer, nullable=False)
)


class ProgressionTrees(Base):
    __tablename__ = 'ProgressionTrees'

    ProgressionTreeType: Mapped[str] = mapped_column(Text, primary_key=True)
    CostProgressionModel: Mapped[str] = mapped_column(Text, nullable=False, server_default=text('"NO_COST_PROGRESSION"'))
    CostProgressionParam1: Mapped[int] = mapped_column(Integer, nullable=False, server_default=text('0'))
    PrereqFormat: Mapped[str] = mapped_column(Text, nullable=False, server_default=text('"AND"'))
    SystemType: Mapped[str] = mapped_column(Text, nullable=False)
    AgeType: Mapped[Optional[str]] = mapped_column(ForeignKey('Ages.AgeType', ondelete='CASCADE', onupdate='CASCADE'))
    IconString: Mapped[Optional[str]] = mapped_column(Text)
    MultipleUnlockName: Mapped[Optional[str]] = mapped_column(Text)
    Name: Mapped[Optional[str]] = mapped_column(Text)
    RevealRequirementSetId: Mapped[Optional[str]] = mapped_column(Text)

    Ages_: Mapped[list['Ages']] = relationship('Ages', foreign_keys='[Ages.MainCultureProgressionTreeType]', back_populates='ProgressionTrees')
    Ages1: Mapped[list['Ages']] = relationship('Ages', foreign_keys='[Ages.MainTechProgressionTreeType]', back_populates='ProgressionTrees_')
    Ages2: Mapped[Optional['Ages']] = relationship('Ages', foreign_keys=[AgeType], back_populates='ProgressionTrees1')
    Attributes: Mapped[list['Attributes']] = relationship('Attributes', back_populates='ProgressionTrees_')
    ProgressionTreeNodes: Mapped[list['ProgressionTreeNodes']] = relationship('ProgressionTreeNodes', back_populates='ProgressionTrees_')
    Civilizations: Mapped[list['Civilizations']] = relationship('Civilizations', back_populates='ProgressionTrees_')
    Ideologies: Mapped[list['Ideologies']] = relationship('Ideologies', back_populates='ProgressionTrees_')


class PseudoYields(Base):
    __tablename__ = 'PseudoYields'

    PseudoYieldType: Mapped[str] = mapped_column(Text, primary_key=True)
    DefaultValue: Mapped[float] = mapped_column(REAL, nullable=False, server_default=text('1'))

    GreatWorkObjectTypes: Mapped[list['GreatWorkObjectTypes']] = relationship('GreatWorkObjectTypes', back_populates='PseudoYields_')
    Strategy_YieldPriorities: Mapped[list['StrategyYieldPriorities']] = relationship('StrategyYieldPriorities', back_populates='PseudoYields_')
    Units: Mapped[list['Units']] = relationship('Units', back_populates='PseudoYields_')
    GreatPersonClasses: Mapped[list['GreatPersonClasses']] = relationship('GreatPersonClasses', back_populates='PseudoYields_')


class RealismSettings(Base):
    __tablename__ = 'RealismSettings'

    RealismSettingType: Mapped[str] = mapped_column(Text, primary_key=True)
    Name: Mapped[str] = mapped_column(Text, nullable=False)
    PercentVolcanoesActive: Mapped[Optional[int]] = mapped_column(Integer)

    RandomEventFrequencies: Mapped[list['RandomEventFrequencies']] = relationship('RandomEventFrequencies', back_populates='RealismSettings_')


class ReportingEvents(Base):
    __tablename__ = 'ReportingEvents'

    Name: Mapped[str] = mapped_column(Text, primary_key=True)


class RequirementSetStrings(Base):
    __tablename__ = 'RequirementSetStrings'

    Context: Mapped[str] = mapped_column(Text, primary_key=True)
    RequirementSetId: Mapped[str] = mapped_column(Text, primary_key=True)
    Text_: Mapped[str] = mapped_column('Text', Text, nullable=False)


class RequirementSets(Base):
    __tablename__ = 'RequirementSets'

    RequirementSetId: Mapped[str] = mapped_column(Text, primary_key=True)
    RequirementSetType: Mapped[str] = mapped_column(Text, nullable=False, server_default=text('"REQUIREMENTSET_TEST_ALL"'))

    Requirements: Mapped[list['Requirements']] = relationship('Requirements', secondary='RequirementSetRequirements', back_populates='RequirementSets_')
    Modifiers: Mapped[list['Modifiers']] = relationship('Modifiers', foreign_keys='[Modifiers.OwnerRequirementSetId]', back_populates='RequirementSets_')
    Modifiers_: Mapped[list['Modifiers']] = relationship('Modifiers', foreign_keys='[Modifiers.SubjectRequirementSetId]', back_populates='RequirementSets1')
    Victories: Mapped[list['Victories']] = relationship('Victories', back_populates='RequirementSets_')
    Defeats: Mapped[list['Defeats']] = relationship('Defeats', back_populates='RequirementSets_')
    UnlockRequirements: Mapped[list['UnlockRequirements']] = relationship('UnlockRequirements', back_populates='RequirementSets_')
    LegacyModifiers: Mapped[list['LegacyModifiers']] = relationship('LegacyModifiers', back_populates='RequirementSets_')


class Requirements(Base):
    __tablename__ = 'Requirements'

    RequirementId: Mapped[str] = mapped_column(Text, primary_key=True)
    AiWeighting: Mapped[float] = mapped_column(REAL, nullable=False, server_default=text('0'))
    Impact: Mapped[int] = mapped_column(Integer, nullable=False, server_default=text('0'))
    Inverse: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=text('0'))
    Likeliness: Mapped[int] = mapped_column(Integer, nullable=False, server_default=text('0'))
    Persistent: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=text('0'))
    ProgressWeight: Mapped[int] = mapped_column(Integer, nullable=False, server_default=text('1'))
    RequirementType: Mapped[str] = mapped_column(Text, nullable=False)
    Reverse: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=text('0'))
    Triggered: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=text('0'))
    BehaviorTree: Mapped[Optional[str]] = mapped_column(Text)

    RequirementSets_: Mapped[list['RequirementSets']] = relationship('RequirementSets', secondary='RequirementSetRequirements', back_populates='Requirements')
    RequirementArguments: Mapped[list['RequirementArguments']] = relationship('RequirementArguments', back_populates='Requirements_')
    RequirementStrings: Mapped[list['RequirementStrings']] = relationship('RequirementStrings', back_populates='Requirements_')


class ResourceDistribution(Base):
    __tablename__ = 'Resource_Distribution'

    AgeType: Mapped[str] = mapped_column(Text, primary_key=True)
    AdditionalCutAmount: Mapped[int] = mapped_column(Integer, nullable=False)
    MaxResourceTypes: Mapped[int] = mapped_column(Integer, nullable=False)
    ResourceTypeMaxPerHemisphere: Mapped[int] = mapped_column(Integer, nullable=False)


class SavingTypes(Base):
    __tablename__ = 'SavingTypes'

    SavingType: Mapped[str] = mapped_column(Text, primary_key=True)


class ScoringCategories(Base):
    __tablename__ = 'ScoringCategories'

    CategoryType: Mapped[str] = mapped_column(Text, primary_key=True)
    Multiplier: Mapped[float] = mapped_column(REAL, nullable=False, server_default=text('1'))
    Name: Mapped[str] = mapped_column(Text, nullable=False)

    ScoringLineItems: Mapped[list['ScoringLineItems']] = relationship('ScoringLineItems', back_populates='ScoringCategories_')


class Seasons(Base):
    __tablename__ = 'Seasons'

    SeasonType: Mapped[str] = mapped_column(Text, primary_key=True)
    Description: Mapped[str] = mapped_column(Text, nullable=False)


class SettlementPreferences(Base):
    __tablename__ = 'SettlementPreferences'

    PreferenceType: Mapped[Optional[str]] = mapped_column(Text, primary_key=True)


class ShapeDefinitions(Base):
    __tablename__ = 'ShapeDefinitions'

    ShapeId: Mapped[int] = mapped_column(Integer, primary_key=True)
    Description: Mapped[str] = mapped_column(Text, nullable=False)
    MaxChildren: Mapped[int] = mapped_column(Integer, nullable=False, server_default=text('0'))
    MinChildren: Mapped[int] = mapped_column(Integer, nullable=False, server_default=text('0'))
    ShapeName: Mapped[str] = mapped_column(Text, nullable=False)

    NodeDefinitions: Mapped[list['NodeDefinitions']] = relationship('NodeDefinitions', back_populates='ShapeDefinitions_')


class TagCategories(Base):
    __tablename__ = 'TagCategories'

    Category: Mapped[str] = mapped_column(Text, primary_key=True)

    Tags: Mapped[list['Tags']] = relationship('Tags', back_populates='TagCategories_')


class TargetTypes(Base):
    __tablename__ = 'TargetTypes'

    TargetType: Mapped[str] = mapped_column(Text, primary_key=True)

    AiOperationDefs: Mapped[list['AiOperationDefs']] = relationship('AiOperationDefs', back_populates='TargetTypes_')


class Terrains(Base):
    __tablename__ = 'Terrains'

    TerrainType: Mapped[str] = mapped_column(Text, primary_key=True)
    Appeal: Mapped[int] = mapped_column(Integer, nullable=False, server_default=text('0'))
    DefenseModifier: Mapped[int] = mapped_column(Integer, nullable=False, server_default=text('0'))
    Hills: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=text('0'))
    Impassable: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=text('0'))
    InfluenceCost: Mapped[int] = mapped_column(Integer, nullable=False)
    Mountain: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=text('0'))
    MovementCost: Mapped[int] = mapped_column(Integer, nullable=False)
    Name: Mapped[str] = mapped_column(Text, nullable=False)
    SightModifier: Mapped[int] = mapped_column(Integer, nullable=False, server_default=text('0'))
    SightThroughModifier: Mapped[int] = mapped_column(Integer, nullable=False, server_default=text('0'))
    Water: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=text('0'))

    Biomes_: Mapped[list['Biomes']] = relationship('Biomes', secondary='Biome_ValidTerrains', back_populates='Terrains')
    CityExpansionTypes_: Mapped[list['CityExpansionTypes']] = relationship('CityExpansionTypes', secondary='CityExpansionValidTerrains', back_populates='Terrains')
    UnitEmbarkationTypes: Mapped[list['UnitEmbarkationTypes']] = relationship('UnitEmbarkationTypes', secondary='EmbarkationValidTerrains', back_populates='Terrains_')
    Constructibles: Mapped[list['Constructibles']] = relationship('Constructibles', back_populates='Terrains_')
    Constructibles_: Mapped[list['Constructibles']] = relationship('Constructibles', secondary='Constructible_ValidTerrains', back_populates='Terrains1')
    Features: Mapped[list['Features']] = relationship('Features', secondary='Feature_AdjacentTerrains', back_populates='Terrains_')
    Features_: Mapped[list['Features']] = relationship('Features', secondary='Feature_NotAdjacentTerrains', back_populates='Terrains1')
    Features1: Mapped[list['Features']] = relationship('Features', secondary='Feature_ValidTerrains', back_populates='Terrains2')
    StartBiasTerrains: Mapped[list['StartBiasTerrains']] = relationship('StartBiasTerrains', back_populates='Terrains_')
    Adjacency_YieldChanges: Mapped[list['AdjacencyYieldChanges']] = relationship('AdjacencyYieldChanges', back_populates='Terrains_')
    RegionClaimObstacles: Mapped[list['RegionClaimObstacles']] = relationship('RegionClaimObstacles', back_populates='Terrains_')
    Resource_ValidBiomes: Mapped[list['ResourceValidBiomes']] = relationship('ResourceValidBiomes', back_populates='Terrains_')
    TerrainBiomeFeature_YieldChanges: Mapped[list['TerrainBiomeFeatureYieldChanges']] = relationship('TerrainBiomeFeatureYieldChanges', back_populates='Terrains_')
    UnitMovementClassObstacles: Mapped[list['UnitMovementClassObstacles']] = relationship('UnitMovementClassObstacles', back_populates='Terrains_')
    Warehouse_YieldChanges: Mapped[list['WarehouseYieldChanges']] = relationship('WarehouseYieldChanges', back_populates='Terrains_')


class TradeSystemParameterSets(Base):
    __tablename__ = 'TradeSystemParameterSets'

    Type: Mapped[str] = mapped_column(Text, primary_key=True)
    BaseResourceCapacity: Mapped[int] = mapped_column(Integer, nullable=False, server_default=text('2'))
    LandRouteRange: Mapped[int] = mapped_column(Integer, nullable=False, server_default=text('10'))
    SeaRouteRange: Mapped[int] = mapped_column(Integer, nullable=False, server_default=text('10'))
    StartRoutesAtDistance: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=text('0'))

    Ages_: Mapped[list['Ages']] = relationship('Ages', back_populates='TradeSystemParameterSets')


class TribeTagSets(Base):
    __tablename__ = 'TribeTagSets'

    TribeTagName: Mapped[str] = mapped_column(Text, primary_key=True)
    InitialUnitAmount: Mapped[int] = mapped_column(Integer, nullable=False, server_default=text('0'))
    MaxUnitAmount: Mapped[int] = mapped_column(Integer, nullable=False, server_default=text('1'))

    IndependentTribeTypes: Mapped[list['IndependentTribeTypes']] = relationship('IndependentTribeTypes', secondary='TribeCombatTagSets', back_populates='TribeTagSets_')
    IndependentTribeTypes_: Mapped[list['IndependentTribeTypes']] = relationship('IndependentTribeTypes', secondary='TribeCommanderTagSets', back_populates='TribeTagSets1')
    IndependentTribeTypes1: Mapped[list['IndependentTribeTypes']] = relationship('IndependentTribeTypes', secondary='TribeScoutTagSets', back_populates='TribeTagSets2')
    TribeCombatTags: Mapped[list['TribeCombatTags']] = relationship('TribeCombatTags', back_populates='TribeTagSets_')
    TribeForbiddenCombatTags: Mapped[list['TribeForbiddenCombatTags']] = relationship('TribeForbiddenCombatTags', back_populates='TribeTagSets_')
    TribeRequiredCombatTags: Mapped[list['TribeRequiredCombatTags']] = relationship('TribeRequiredCombatTags', back_populates='TribeTagSets_')
    IndependentTribeTypes2: Mapped[list['IndependentTribeTypes']] = relationship('IndependentTribeTypes', back_populates='TribeTagSets3')


class TurnSegments(Base):
    __tablename__ = 'TurnSegments'

    TurnSegmentType: Mapped[str] = mapped_column(Text, primary_key=True)
    AllowStrategicCommands: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=text('0'))
    AllowTacticalCommands: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=text('0'))
    AllowTurnUnready: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=text('1'))
    TimeLimit_Base: Mapped[int] = mapped_column(Integer, nullable=False, server_default=text('0'))
    TimeLimit_PerCity: Mapped[int] = mapped_column(Integer, nullable=False, server_default=text('0'))
    TimeLimit_PerUnit: Mapped[int] = mapped_column(Integer, nullable=False, server_default=text('0'))
    Name: Mapped[Optional[str]] = mapped_column(Text)
    Sound: Mapped[Optional[str]] = mapped_column(Text)

    TurnPhases: Mapped[list['TurnPhases']] = relationship('TurnPhases', foreign_keys='[TurnPhases.ActiveSegmentType]', back_populates='TurnSegments_')
    TurnPhases_: Mapped[list['TurnPhases']] = relationship('TurnPhases', foreign_keys='[TurnPhases.InactiveSegmentType]', back_populates='TurnSegments1')


class TurnTimers(Base):
    __tablename__ = 'TurnTimers'

    TurnTimerType: Mapped[str] = mapped_column(Text, primary_key=True)
    Description: Mapped[str] = mapped_column(Text, nullable=False)
    Name: Mapped[str] = mapped_column(Text, nullable=False)


class TypeToDiplomacyStatements(Base):
    __tablename__ = 'TypeToDiplomacyStatements'

    Type: Mapped[str] = mapped_column(Text, primary_key=True)
    DiplomacyStatementType: Mapped[str] = mapped_column(Text, nullable=False)


class UnhappinessEffects(Base):
    __tablename__ = 'UnhappinessEffects'

    ID: Mapped[str] = mapped_column(Text, primary_key=True)
    Amount: Mapped[int] = mapped_column(Integer, nullable=False)
    CategoryText: Mapped[str] = mapped_column(Text, nullable=False)
    Condition: Mapped[str] = mapped_column(Text, nullable=False)
    Description: Mapped[str] = mapped_column(Text, nullable=False)
    Duration: Mapped[Optional[int]] = mapped_column(Integer)
    Ongoing: Mapped[Optional[bool]] = mapped_column(Boolean, server_default=text('0'))
    ScaleBySpeed: Mapped[Optional[bool]] = mapped_column(Boolean, server_default=text('0'))


class UnitAiTypes(Base):
    __tablename__ = 'UnitAiTypes'

    AiType: Mapped[str] = mapped_column(Text, primary_key=True)
    Priority: Mapped[Optional[bool]] = mapped_column(Boolean, server_default=text('0'))
    TypeValue: Mapped[Optional[int]] = mapped_column(Integer)

    Units: Mapped[list['Units']] = relationship('Units', secondary='UnitAiInfos', back_populates='UnitAiTypes_')


class UnitEmbarkationTypes(Base):
    __tablename__ = 'UnitEmbarkationTypes'

    EmbarkationType: Mapped[str] = mapped_column(Text, primary_key=True)
    Name: Mapped[str] = mapped_column(Text, nullable=False)

    Terrains_: Mapped[list['Terrains']] = relationship('Terrains', secondary='EmbarkationValidTerrains', back_populates='UnitEmbarkationTypes')


class UnitFormationClasses(Base):
    __tablename__ = 'UnitFormationClasses'

    FormationClassType: Mapped[str] = mapped_column(Text, primary_key=True)
    Name: Mapped[str] = mapped_column(Text, nullable=False)


class UnitNames(Base):
    __tablename__ = 'UnitNames'

    ID: Mapped[int] = mapped_column(Integer, primary_key=True)
    NameType: Mapped[str] = mapped_column(Text, nullable=False)
    TextKey: Mapped[str] = mapped_column(Text, nullable=False)


class UnitRebellionTags(Base):
    __tablename__ = 'Unit_RebellionTags'

    RebellionLevel: Mapped[int] = mapped_column(Integer, primary_key=True)
    Tag: Mapped[str] = mapped_column(Text, primary_key=True)
    NumCreated: Mapped[int] = mapped_column(Integer, nullable=False, server_default=text('1'))
    ForbiddenTag: Mapped[Optional[str]] = mapped_column(Text)


class UnitTransitionShadows(Base):
    __tablename__ = 'Unit_TransitionShadows'

    Tag: Mapped[str] = mapped_column(Text, primary_key=True)
    CoreClass: Mapped[str] = mapped_column(Text, nullable=False)
    Domain: Mapped[str] = mapped_column(Text, nullable=False)


class UnlockRewards(Base):
    __tablename__ = 'UnlockRewards'

    Name: Mapped[str] = mapped_column(Text, primary_key=True)
    UnlockType: Mapped[str] = mapped_column(Text, primary_key=True)
    Description: Mapped[Optional[str]] = mapped_column(Text)
    Icon: Mapped[Optional[str]] = mapped_column(Text)
    UnlockRewardKind: Mapped[Optional[str]] = mapped_column(Text)
    UnlockRewardType: Mapped[Optional[str]] = mapped_column(Text)


class VictoryClasses(Base):
    __tablename__ = 'VictoryClasses'

    VictoryClassType: Mapped[str] = mapped_column(Text, primary_key=True)
    Name: Mapped[str] = mapped_column(Text, nullable=False)

    Victories: Mapped[list['Victories']] = relationship('Victories', back_populates='VictoryClasses_')


class VictoryScorings(Base):
    __tablename__ = 'VictoryScorings'

    ScoringId: Mapped[str] = mapped_column(Text, primary_key=True)
    Name: Mapped[str] = mapped_column(Text, nullable=False)
    Points: Mapped[int] = mapped_column(Integer, nullable=False, server_default=text('0'))
    ScoringType: Mapped[str] = mapped_column(Text, nullable=False)
    StaticCarryover: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=text('0'))
    VictoryType: Mapped[str] = mapped_column(Text, nullable=False)
    Data: Mapped[Optional[str]] = mapped_column(Text)


class VictoryTypes(Base):
    __tablename__ = 'VictoryTypes'

    VictoryType: Mapped[str] = mapped_column(Text, primary_key=True)
    CountdownDuration: Mapped[int] = mapped_column(Integer, nullable=False, server_default=text('-1'))
    Description: Mapped[str] = mapped_column(Text, nullable=False)
    DominationAmount: Mapped[int] = mapped_column(Integer, nullable=False, server_default=text('-1'))
    DominationPercent: Mapped[int] = mapped_column(Integer, nullable=False, server_default=text('-1'))
    FinalAge: Mapped[str] = mapped_column(Text, nullable=False)
    Name: Mapped[str] = mapped_column(Text, nullable=False)
    PrereqRequirementSetId: Mapped[Optional[str]] = mapped_column(Text)

    Strategies: Mapped[list['Strategies']] = relationship('Strategies', back_populates='VictoryTypes_')


class WMDs(Base):
    __tablename__ = 'WMDs'

    WeaponType: Mapped[str] = mapped_column(Text, primary_key=True)
    AffectBuildings: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=text('0'))
    AffectImprovements: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=text('0'))
    AffectPopulation: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=text('0'))
    AffectResources: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=text('0'))
    AffectRoutes: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=text('0'))
    AffectUnits: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=text('0'))
    BlastRadius: Mapped[int] = mapped_column(Integer, nullable=False, server_default=text('1'))
    FalloutDuration: Mapped[int] = mapped_column(Integer, nullable=False, server_default=text('0'))
    ICBMStrikeRange: Mapped[int] = mapped_column(Integer, nullable=False, server_default=text('0'))
    Maintenance: Mapped[int] = mapped_column(Integer, nullable=False, server_default=text('0'))
    Name: Mapped[str] = mapped_column(Text, nullable=False)

    Unit_Stats: Mapped[list['UnitStats']] = relationship('UnitStats', back_populates='WMDs_')


class WarWearinessEffects(Base):
    __tablename__ = 'WarWearinessEffects'

    WarWearinessType: Mapped[str] = mapped_column(Text, primary_key=True)
    MaxYieldReduction: Mapped[int] = mapped_column(Integer, nullable=False)
    YieldReductionPerLevel: Mapped[int] = mapped_column(Integer, nullable=False)


class Wars(Base):
    __tablename__ = 'Wars'

    WarType: Mapped[str] = mapped_column(Text, primary_key=True)
    Description: Mapped[Optional[str]] = mapped_column(Text)
    Name: Mapped[Optional[str]] = mapped_column(Text)


class Yields(Base):
    __tablename__ = 'Yields'

    YieldType: Mapped[str] = mapped_column(Text, primary_key=True)
    DefaultValue: Mapped[float] = mapped_column(REAL, nullable=False, server_default=text('1'))
    IconString: Mapped[str] = mapped_column(Text, nullable=False)
    Name: Mapped[str] = mapped_column(Text, nullable=False)
    OccupiedCityChange: Mapped[float] = mapped_column(REAL, nullable=False, server_default=text('0'))

    AiBuildSpecializations: Mapped[list['AiBuildSpecializations']] = relationship('AiBuildSpecializations', foreign_keys='[AiBuildSpecializations.BuildingYield]', back_populates='Yields_')
    AiBuildSpecializations_: Mapped[list['AiBuildSpecializations']] = relationship('AiBuildSpecializations', foreign_keys='[AiBuildSpecializations.PrioritizationYield]', back_populates='Yields1')
    TradeYields: Mapped[list['TradeYields']] = relationship('TradeYields', back_populates='Yields_')
    NarrativeStories: Mapped[list['NarrativeStories']] = relationship('NarrativeStories', back_populates='Yields_')
    Strategy_YieldPriorities: Mapped[list['StrategyYieldPriorities']] = relationship('StrategyYieldPriorities', back_populates='Yields_')
    Adjacency_YieldChanges: Mapped[list['AdjacencyYieldChanges']] = relationship('AdjacencyYieldChanges', back_populates='Yields_')
    Buildings: Mapped[list['Buildings']] = relationship('Buildings', back_populates='Yields_')
    Constructible_CitizenYieldChanges: Mapped[list['ConstructibleCitizenYieldChanges']] = relationship('ConstructibleCitizenYieldChanges', back_populates='Yields_')
    Constructible_Maintenances: Mapped[list['ConstructibleMaintenances']] = relationship('ConstructibleMaintenances', back_populates='Yields_')
    Constructible_YieldChanges: Mapped[list['ConstructibleYieldChanges']] = relationship('ConstructibleYieldChanges', back_populates='Yields_')
    Feature_CityYields: Mapped[list['FeatureCityYields']] = relationship('FeatureCityYields', back_populates='Yields_')
    Feature_Removes: Mapped[list['FeatureRemoves']] = relationship('FeatureRemoves', back_populates='Yields_')
    Resource_Harvests: Mapped[list['ResourceHarvests']] = relationship('ResourceHarvests', back_populates='Yields_')
    Resource_YieldChanges: Mapped[list['ResourceYieldChanges']] = relationship('ResourceYieldChanges', back_populates='Yields_')
    TerrainBiomeFeature_YieldChanges: Mapped[list['TerrainBiomeFeatureYieldChanges']] = relationship('TerrainBiomeFeatureYieldChanges', back_populates='Yields_')
    Units: Mapped[list['Units']] = relationship('Units', back_populates='Yields_')
    Warehouse_YieldChanges: Mapped[list['WarehouseYieldChanges']] = relationship('WarehouseYieldChanges', back_populates='Yields_')
    Project_YieldConversions: Mapped[list['ProjectYieldConversions']] = relationship('ProjectYieldConversions', back_populates='Yields_')
    RandomEventYields: Mapped[list['RandomEventYields']] = relationship('RandomEventYields', back_populates='Yields_')
    Unit_Costs: Mapped[list['UnitCosts']] = relationship('UnitCosts', back_populates='Yields_')
    GreatWork_YieldChanges: Mapped[list['GreatWorkYieldChanges']] = relationship('GreatWorkYieldChanges', back_populates='Yields_')


class AdvancedStartAges(Ages):
    __tablename__ = 'AdvancedStartAges'

    AgeType: Mapped[str] = mapped_column(ForeignKey('Ages.AgeType', ondelete='CASCADE', onupdate='CASCADE'), primary_key=True)
    AdvancedStartRevealPastOcean: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=text('0'))
    AdvancedStartVisibilityRadius: Mapped[int] = mapped_column(Integer, nullable=False, server_default=text('1'))
    Gold: Mapped[int] = mapped_column(Integer, nullable=False, server_default=text('0'))
    GoldCityState: Mapped[int] = mapped_column(Integer, nullable=False, server_default=text('0'))
    NewTownRuralPlots: Mapped[int] = mapped_column(Integer, nullable=False, server_default=text('1'))
    ObsoleteBuildingReplacementRewardWorkers: Mapped[int] = mapped_column(Integer, nullable=False, server_default=text('1'))
    StartCities: Mapped[int] = mapped_column(Integer, nullable=False)
    StartingWorkersMajor: Mapped[int] = mapped_column(Integer, nullable=False, server_default=text('0'))
    Year: Mapped[int] = mapped_column(Integer, nullable=False)


class AdvancedStartCardEffects(Base):
    __tablename__ = 'AdvancedStartCardEffects'

    EffectID: Mapped[str] = mapped_column(Text, primary_key=True)
    Age: Mapped[str] = mapped_column(ForeignKey('Ages.AgeType', ondelete='CASCADE', onupdate='CASCADE'), nullable=False)
    Amount: Mapped[int] = mapped_column(Integer, nullable=False, server_default=text('0'))
    EffectType: Mapped[str] = mapped_column(Text, nullable=False)
    IsPlacementEffect: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=text('0'))
    Description: Mapped[Optional[str]] = mapped_column(Text)
    DidNotPlaceEffectType: Mapped[Optional[str]] = mapped_column(Text)
    Name: Mapped[Optional[str]] = mapped_column(Text)
    Special: Mapped[Optional[int]] = mapped_column(Integer, server_default=text('0'))

    Ages_: Mapped['Ages'] = relationship('Ages', back_populates='AdvancedStartCardEffects')


class AdvancedStartCardSets(Base):
    __tablename__ = 'AdvancedStartCardSets'

    CardSet: Mapped[str] = mapped_column(Text, primary_key=True)
    Age: Mapped[str] = mapped_column(ForeignKey('Ages.AgeType', ondelete='CASCADE', onupdate='CASCADE'), nullable=False)
    DefaultSet: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=text('0'))
    Name: Mapped[str] = mapped_column(Text, nullable=False)

    Ages_: Mapped['Ages'] = relationship('Ages', back_populates='AdvancedStartCardSets')


class AdvancedStartCards(Base):
    __tablename__ = 'AdvancedStartCards'

    CardID: Mapped[str] = mapped_column(Text, primary_key=True)
    Age: Mapped[str] = mapped_column(ForeignKey('Ages.AgeType', ondelete='CASCADE', onupdate='CASCADE'), nullable=False)
    CardEffectType1: Mapped[str] = mapped_column(Text, nullable=False)
    CardSet: Mapped[str] = mapped_column(Text, nullable=False)
    CategorySortOrder: Mapped[int] = mapped_column(Integer, nullable=False, server_default=text('0'))
    CultureCost: Mapped[int] = mapped_column(Integer, nullable=False, server_default=text('0'))
    DarkAgeCost: Mapped[int] = mapped_column(Integer, nullable=False, server_default=text('0'))
    Description: Mapped[str] = mapped_column(Text, nullable=False)
    EconomicCost: Mapped[int] = mapped_column(Integer, nullable=False, server_default=text('0'))
    MilitaristicCost: Mapped[int] = mapped_column(Integer, nullable=False, server_default=text('0'))
    Name: Mapped[str] = mapped_column(Text, nullable=False)
    ScienceCost: Mapped[int] = mapped_column(Integer, nullable=False, server_default=text('0'))
    WildcardCost: Mapped[int] = mapped_column(Integer, nullable=False, server_default=text('0'))
    CardEffectType2: Mapped[Optional[str]] = mapped_column(Text)
    CardEffectType3: Mapped[Optional[str]] = mapped_column(Text)
    CardEffectType4: Mapped[Optional[str]] = mapped_column(Text)
    GoldenAgeReward: Mapped[Optional[bool]] = mapped_column(Boolean, server_default=text('0'))
    GroupLimit: Mapped[Optional[int]] = mapped_column(Integer, server_default=text('-1'))
    IndividualLimit: Mapped[Optional[int]] = mapped_column(Integer, server_default=text('-1'))
    LimitID: Mapped[Optional[str]] = mapped_column(Text, server_default=text('""'))
    Tooltip: Mapped[Optional[str]] = mapped_column(Text)
    UniqueCiv: Mapped[Optional[str]] = mapped_column(Text)
    UniqueLeader: Mapped[Optional[str]] = mapped_column(Text)
    Unlock: Mapped[Optional[str]] = mapped_column(Text)

    Ages_: Mapped['Ages'] = relationship('Ages', back_populates='AdvancedStartCards')
    AdvancedStartDecks_: Mapped[list['AdvancedStartDecks']] = relationship('AdvancedStartDecks', secondary='AdvancedStartDeckCardEntries', back_populates='AdvancedStartCards')
    AdvancedStartAIModifiers: Mapped[list['AdvancedStartAIModifiers']] = relationship('AdvancedStartAIModifiers', back_populates='AdvancedStartCards_')


class AdvancedStartParameters(Base):
    __tablename__ = 'AdvancedStartParameters'

    Age: Mapped[str] = mapped_column(ForeignKey('Ages.AgeType', ondelete='CASCADE', onupdate='CASCADE'), primary_key=True)
    CardLimit: Mapped[int] = mapped_column(Integer, nullable=False, server_default=text('0'))
    DeckLimit: Mapped[int] = mapped_column(Integer, nullable=False, server_default=text('0'))
    FreeUnits: Mapped[int] = mapped_column(Integer, nullable=False, server_default=text('0'))
    MaxRegionPlots: Mapped[int] = mapped_column(Integer, nullable=False, server_default=text('0'))
    RevealType: Mapped[str] = mapped_column(Text, nullable=False)
    ShowRegion: Mapped[int] = mapped_column(Integer, nullable=False, server_default=text('0'))


class AdvancedStartTowns(Base):
    __tablename__ = 'AdvancedStartTowns'

    Age: Mapped[str] = mapped_column(ForeignKey('Ages.AgeType', ondelete='CASCADE', onupdate='CASCADE'), primary_key=True)
    TownID: Mapped[int] = mapped_column(Integer, primary_key=True)
    Capital: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=text('0'))
    City: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=text('0'))
    RuralPopulation: Mapped[int] = mapped_column(Integer, nullable=False)
    UrbanPopulation: Mapped[int] = mapped_column(Integer, nullable=False)
    WorkerPopulation: Mapped[int] = mapped_column(Integer, nullable=False, server_default=text('0'))

    Ages_: Mapped['Ages'] = relationship('Ages', back_populates='AdvancedStartTowns')


class AdvisorSubjects(Base):
    __tablename__ = 'AdvisorSubjects'

    AdvisorType: Mapped[str] = mapped_column(ForeignKey('Advisors.AdvisorType', ondelete='CASCADE', onupdate='CASCADE'), primary_key=True)
    AdvisoryClassType: Mapped[str] = mapped_column(ForeignKey('AdvisoryClasses.AdvisoryClassType', ondelete='CASCADE', onupdate='CASCADE'), primary_key=True)
    AdvisorySubjectType: Mapped[str] = mapped_column(ForeignKey('AdvisorySubjects.AdvisorySubjectType', ondelete='CASCADE', onupdate='CASCADE'), primary_key=True)

    Advisors_: Mapped['Advisors'] = relationship('Advisors', back_populates='AdvisorSubjects')
    AdvisoryClasses_: Mapped['AdvisoryClasses'] = relationship('AdvisoryClasses', back_populates='AdvisorSubjects')
    AdvisorySubjects_: Mapped['AdvisorySubjects'] = relationship('AdvisorySubjects', back_populates='AdvisorSubjects')


class AdvisorWarnings(Base):
    __tablename__ = 'AdvisorWarnings'

    AdvisorWarningType: Mapped[str] = mapped_column(Text, primary_key=True)
    AdvisorType: Mapped[str] = mapped_column(Text, nullable=False)
    CooldownTurns: Mapped[int] = mapped_column(Integer, nullable=False, server_default=text('0'))
    MaxAgePercentComplete: Mapped[int] = mapped_column(Integer, nullable=False, server_default=text('100'))
    MinAgePercentComplete: Mapped[int] = mapped_column(Integer, nullable=False, server_default=text('0'))
    NotificationLevel: Mapped[int] = mapped_column(Integer, nullable=False)
    NotificationType: Mapped[str] = mapped_column(Text, nullable=False)
    Repeatable: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=text('0'))
    SpecificItemCooldownTurns: Mapped[int] = mapped_column(Integer, nullable=False, server_default=text('0'))
    Description: Mapped[Optional[str]] = mapped_column(Text)
    MaxDifficulty: Mapped[Optional[str]] = mapped_column(ForeignKey('Difficulties.DifficultyType', ondelete='CASCADE', onupdate='CASCADE'))
    Name: Mapped[Optional[str]] = mapped_column(Text)

    Difficulties_: Mapped[Optional['Difficulties']] = relationship('Difficulties', back_populates='AdvisorWarnings')


class AgeConstructibleDefaultMaintenances(Base):
    __tablename__ = 'AgeConstructibleDefaultMaintenances'

    Age: Mapped[str] = mapped_column(ForeignKey('Ages.AgeType', ondelete='CASCADE', onupdate='CASCADE'), primary_key=True)
    YieldChange: Mapped[int] = mapped_column(Integer, nullable=False)


class AgeConstructibleDefaultYields(Base):
    __tablename__ = 'AgeConstructibleDefaultYields'

    Age: Mapped[str] = mapped_column(ForeignKey('Ages.AgeType', ondelete='CASCADE', onupdate='CASCADE'), primary_key=True)
    YieldChange: Mapped[int] = mapped_column(Integer, nullable=False)


class AgeCrises(Base):
    __tablename__ = 'AgeCrises'

    AgeCrisisType: Mapped[str] = mapped_column(Text, primary_key=True)
    AgeProgressionType: Mapped[str] = mapped_column(ForeignKey('AgeProgressions.AgeProgressionType', ondelete='CASCADE', onupdate='CASCADE'), nullable=False)

    AgeProgressions_: Mapped['AgeProgressions'] = relationship('AgeProgressions', back_populates='AgeCrises')
    AgeCrisisEvents: Mapped[list['AgeCrisisEvents']] = relationship('AgeCrisisEvents', back_populates='AgeCrises_')


class AgeGrowthBalances(Base):
    __tablename__ = 'AgeGrowthBalances'

    Age: Mapped[str] = mapped_column(ForeignKey('Ages.AgeType', ondelete='CASCADE', onupdate='CASCADE'), primary_key=True)
    Exponent: Mapped[int] = mapped_column(Integer, nullable=False)
    Flat: Mapped[int] = mapped_column(Integer, nullable=False)
    Scalar: Mapped[int] = mapped_column(Integer, nullable=False)


class AgeProgressionEvents(Base):
    __tablename__ = 'AgeProgressionEvents'

    AgeProgressionEventType: Mapped[str] = mapped_column(Text, primary_key=True)
    AgeProgressionType: Mapped[str] = mapped_column(ForeignKey('AgeProgressions.AgeProgressionType', ondelete='CASCADE', onupdate='CASCADE'), nullable=False)
    GameSpeedScaling: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=text('1'))
    Points: Mapped[int] = mapped_column(Integer, nullable=False, server_default=text('0'))

    AgeProgressions_: Mapped['AgeProgressions'] = relationship('AgeProgressions', back_populates='AgeProgressionEvents')
    AgeProgressionEventMapSizeOverrides: Mapped[list['AgeProgressionEventMapSizeOverrides']] = relationship('AgeProgressionEventMapSizeOverrides', back_populates='AgeProgressionEvents_')
    AgeProgressionMilestones: Mapped[list['AgeProgressionMilestones']] = relationship('AgeProgressionMilestones', back_populates='AgeProgressionEvents_')


t_AgeProgressionNotifications = Table(
    'AgeProgressionNotifications', Base.metadata,
    Column('MessageText', Text, nullable=False),
    Column('NotificationType', ForeignKey('Notifications.NotificationType', ondelete='CASCADE', onupdate='CASCADE'), nullable=False),
    Column('PercentComplete', Integer, nullable=False, server_default=text('0')),
    Column('SummaryText', Text, nullable=False)
)


class AgeProgressionTurns(Base):
    __tablename__ = 'AgeProgressionTurns'

    AgeProgressionTurnType: Mapped[str] = mapped_column(Text, primary_key=True)
    AgeProgressionType: Mapped[str] = mapped_column(ForeignKey('AgeProgressions.AgeProgressionType', ondelete='CASCADE', onupdate='CASCADE'), nullable=False)
    GameSpeedScaling: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=text('1'))
    Points: Mapped[int] = mapped_column(Integer, nullable=False, server_default=text('0'))

    AgeProgressions_: Mapped['AgeProgressions'] = relationship('AgeProgressions', back_populates='AgeProgressionTurns')


class AgeTransitionBoostableNodes(Base):
    __tablename__ = 'AgeTransitionBoostableNodes'

    Modifier: Mapped[str] = mapped_column(Text, primary_key=True)
    Age: Mapped[str] = mapped_column(ForeignKey('Ages.AgeType', ondelete='CASCADE', onupdate='CASCADE'), nullable=False)
    Tree: Mapped[str] = mapped_column(Text, nullable=False)

    Ages_: Mapped['Ages'] = relationship('Ages', back_populates='AgeTransitionBoostableNodes')


class AgeTransitionCardSets(Base):
    __tablename__ = 'AgeTransitionCardSets'

    CardSet: Mapped[str] = mapped_column(Text, primary_key=True)
    Age: Mapped[str] = mapped_column(ForeignKey('Ages.AgeType', ondelete='CASCADE', onupdate='CASCADE'), nullable=False)
    DefaultSet: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=text('0'))
    Name: Mapped[str] = mapped_column(Text, nullable=False)

    Ages_: Mapped['Ages'] = relationship('Ages', back_populates='AgeTransitionCardSets')


t_AgeTransitionLegacyPoints = Table(
    'AgeTransitionLegacyPoints', Base.metadata,
    Column('Age', ForeignKey('Ages.AgeType', ondelete='CASCADE', onupdate='CASCADE'), nullable=False),
    Column('Amount', Integer, nullable=False, server_default=text('0')),
    Column('PointType', Text, nullable=False),
    Column('Unlock', Text)
)


class AgeTransitionParameters(Base):
    __tablename__ = 'AgeTransitionParameters'

    Setting: Mapped[str] = mapped_column(Text, primary_key=True)
    Age: Mapped[str] = mapped_column(ForeignKey('Ages.AgeType', ondelete='CASCADE', onupdate='CASCADE'), nullable=False)
    CityCountOnTransition: Mapped[int] = mapped_column(Integer, nullable=False)
    CommanderCountOnTransition: Mapped[int] = mapped_column(Integer, nullable=False)
    DefaultGoldOnTransition: Mapped[int] = mapped_column(Integer, nullable=False)
    GoldGainOnTransition: Mapped[int] = mapped_column(Integer, nullable=False)
    SettlementCountOnTransition: Mapped[int] = mapped_column(Integer, nullable=False)
    WonderCountOnTransition: Mapped[int] = mapped_column(Integer, nullable=False)

    Ages_: Mapped['Ages'] = relationship('Ages', back_populates='AgeTransitionParameters')


class AiBuildSpecializations(Base):
    __tablename__ = 'AiBuildSpecializations'

    PrioritizationYield: Mapped[str] = mapped_column(ForeignKey('Yields.YieldType', ondelete='CASCADE', onupdate='CASCADE'), primary_key=True)
    SpecializationType: Mapped[str] = mapped_column(Text, primary_key=True)
    IncludeDefense: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=text('0'))
    IncludeMilitaryUnits: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=text('0'))
    IncludePopulation: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=text('0'))
    PriorityOffset: Mapped[int] = mapped_column(Integer, nullable=False, server_default=text('0'))
    BuildingYield: Mapped[Optional[str]] = mapped_column(ForeignKey('Yields.YieldType', ondelete='CASCADE', onupdate='CASCADE'))

    Yields_: Mapped[Optional['Yields']] = relationship('Yields', foreign_keys=[BuildingYield], back_populates='AiBuildSpecializations')
    Yields1: Mapped['Yields'] = relationship('Yields', foreign_keys=[PrioritizationYield], back_populates='AiBuildSpecializations_')


class AiComponents(Base):
    __tablename__ = 'AiComponents'

    Component: Mapped[str] = mapped_column(Text, primary_key=True)
    Broker: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=text('0'))
    Consumer: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=text('0'))
    Producer: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=text('0'))
    DefaultPriority: Mapped[Optional[str]] = mapped_column(ForeignKey('AiPriorities.Priority', ondelete='CASCADE', onupdate='CASCADE'), server_default=text('"AI_PRIORITY_MEDIUM"'))

    AiPriorities_: Mapped[Optional['AiPriorities']] = relationship('AiPriorities', back_populates='AiComponents')
    AiDefinitions: Mapped[list['AiDefinitions']] = relationship('AiDefinitions', back_populates='AiComponents_')


class AiFavoredItems(Base):
    __tablename__ = 'AiFavoredItems'

    Favored: Mapped[bool] = mapped_column(Boolean, primary_key=True, server_default=text('1'))
    Item: Mapped[str] = mapped_column(Text, primary_key=True)
    Value: Mapped[int] = mapped_column(Integer, primary_key=True, server_default=text('0'))
    ListType: Mapped[Optional[str]] = mapped_column(ForeignKey('AiListTypes.ListType', ondelete='CASCADE', onupdate='CASCADE'), primary_key=True, nullable=True)
    StringVal: Mapped[Optional[str]] = mapped_column(Text, primary_key=True, nullable=True)
    MaxDifficulty: Mapped[Optional[str]] = mapped_column(ForeignKey('Difficulties.DifficultyType', ondelete='CASCADE', onupdate='CASCADE'))
    MinDifficulty: Mapped[Optional[str]] = mapped_column(ForeignKey('Difficulties.DifficultyType', ondelete='CASCADE', onupdate='CASCADE'))
    TooltipString: Mapped[Optional[str]] = mapped_column(Text)

    AiListTypes_: Mapped[Optional['AiListTypes']] = relationship('AiListTypes', back_populates='AiFavoredItems')
    Difficulties_: Mapped[Optional['Difficulties']] = relationship('Difficulties', foreign_keys=[MaxDifficulty], back_populates='AiFavoredItems')
    Difficulties1: Mapped[Optional['Difficulties']] = relationship('Difficulties', foreign_keys=[MinDifficulty], back_populates='AiFavoredItems_')


class AiLists(Base):
    __tablename__ = 'AiLists'

    ListType: Mapped[str] = mapped_column(ForeignKey('AiListTypes.ListType', ondelete='CASCADE', onupdate='CASCADE'), primary_key=True)
    System: Mapped[str] = mapped_column(Text, nullable=False)
    LeaderType: Mapped[Optional[str]] = mapped_column(Text, primary_key=True, nullable=True)
    MaxDifficulty: Mapped[Optional[str]] = mapped_column(ForeignKey('Difficulties.DifficultyType', ondelete='CASCADE', onupdate='CASCADE'))
    MinDifficulty: Mapped[Optional[str]] = mapped_column(ForeignKey('Difficulties.DifficultyType', ondelete='CASCADE', onupdate='CASCADE'))

    AiListTypes_: Mapped['AiListTypes'] = relationship('AiListTypes', back_populates='AiLists')
    Difficulties_: Mapped[Optional['Difficulties']] = relationship('Difficulties', foreign_keys=[MaxDifficulty], back_populates='AiLists')
    Difficulties1: Mapped[Optional['Difficulties']] = relationship('Difficulties', foreign_keys=[MinDifficulty], back_populates='AiLists_')


class AiOperationDefs(Base):
    __tablename__ = 'AiOperationDefs'

    OperationName: Mapped[str] = mapped_column(Text, primary_key=True)
    AllowTargetUpdate: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=text('1'))
    EnemyType: Mapped[str] = mapped_column(Text, nullable=False, server_default=text('"NONE"'))
    MaxTargetDefense: Mapped[int] = mapped_column(Integer, nullable=False, server_default=text('-1'))
    MaxTargetDistInArea: Mapped[int] = mapped_column(Integer, nullable=False, server_default=text('5'))
    MaxTargetDistInRegion: Mapped[int] = mapped_column(Integer, nullable=False, server_default=text('10'))
    MaxTargetDistInWorld: Mapped[int] = mapped_column(Integer, nullable=False, server_default=text('0'))
    MaxTargetStrength: Mapped[int] = mapped_column(Integer, nullable=False, server_default=text('-1'))
    MinOddsOfSuccess: Mapped[float] = mapped_column(REAL, nullable=False, server_default=text('0'))
    MustBeAtWar: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=text('0'))
    MustBeCoastal: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=text('0'))
    MustHaveNukes: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=text('0'))
    MustHaveUnits: Mapped[int] = mapped_column(Integer, nullable=False, server_default=text('-1'))
    Priority: Mapped[int] = mapped_column(Integer, nullable=False, server_default=text('3'))
    SelfStart: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=text('0'))
    TargetParameter: Mapped[int] = mapped_column(Integer, nullable=False, server_default=text('0'))
    TargetType: Mapped[str] = mapped_column(ForeignKey('TargetTypes.TargetType', ondelete='CASCADE', onupdate='CASCADE'), nullable=False)
    BehaviorTree: Mapped[Optional[str]] = mapped_column(ForeignKey('BehaviorTrees.TreeName', ondelete='CASCADE', onupdate='CASCADE'))
    OperationType: Mapped[Optional[str]] = mapped_column(ForeignKey('AiOperationTypes.OperationType', ondelete='CASCADE', onupdate='CASCADE'))
    TargetScript: Mapped[Optional[str]] = mapped_column(Text)

    BehaviorTrees_: Mapped[Optional['BehaviorTrees']] = relationship('BehaviorTrees', back_populates='AiOperationDefs')
    AiOperationTypes_: Mapped[Optional['AiOperationTypes']] = relationship('AiOperationTypes', back_populates='AiOperationDefs')
    TargetTypes_: Mapped['TargetTypes'] = relationship('TargetTypes', back_populates='AiOperationDefs')
    AiOperationTeams: Mapped[list['AiOperationTeams']] = relationship('AiOperationTeams', back_populates='AiOperationDefs_')
    AllowedOperations: Mapped[list['AllowedOperations']] = relationship('AllowedOperations', back_populates='AiOperationDefs_')
    BoostHandlers: Mapped[list['BoostHandlers']] = relationship('BoostHandlers', back_populates='AiOperationDefs_')


class AiOperationLimits(Base):
    __tablename__ = 'AiOperationLimits'

    ListType: Mapped[str] = mapped_column(ForeignKey('AiOperationLists.ListType', ondelete='CASCADE', onupdate='CASCADE'), primary_key=True)
    OperationType: Mapped[str] = mapped_column(ForeignKey('AiOperationTypes.OperationType', ondelete='CASCADE', onupdate='CASCADE'), primary_key=True)
    BaseValue: Mapped[Optional[int]] = mapped_column(Integer)
    DeltaValue: Mapped[Optional[int]] = mapped_column(Integer)

    AiOperationLists_: Mapped['AiOperationLists'] = relationship('AiOperationLists', back_populates='AiOperationLimits')
    AiOperationTypes_: Mapped['AiOperationTypes'] = relationship('AiOperationTypes', back_populates='AiOperationLimits')


class AiTactics(Base):
    __tablename__ = 'AiTactics'

    TacticType: Mapped[str] = mapped_column(Text, primary_key=True)
    DefaultPriority: Mapped[Optional[str]] = mapped_column(ForeignKey('AiPriorities.Priority', ondelete='CASCADE', onupdate='CASCADE'))

    AiPriorities_: Mapped[Optional['AiPriorities']] = relationship('AiPriorities', back_populates='AiTactics')


class Attributes(Base):
    __tablename__ = 'Attributes'

    AttributeType: Mapped[str] = mapped_column(Text, primary_key=True)
    Name: Mapped[str] = mapped_column(Text, nullable=False)
    Description: Mapped[Optional[str]] = mapped_column(Text)
    ProgressionTreeType: Mapped[Optional[str]] = mapped_column(ForeignKey('ProgressionTrees.ProgressionTreeType', ondelete='CASCADE', onupdate='CASCADE'))

    ProgressionTrees_: Mapped[Optional['ProgressionTrees']] = relationship('ProgressionTrees', back_populates='Attributes')
    Governments_: Mapped[list['Governments']] = relationship('Governments', secondary='GovernmentAttributes', back_populates='Attributes')
    Traditions: Mapped[list['Traditions']] = relationship('Traditions', secondary='TraditionAttributes', back_populates='Attributes_')
    Constructible_AttributePoints: Mapped[list['ConstructibleAttributePoints']] = relationship('ConstructibleAttributePoints', back_populates='Attributes_')


class BarbarianAttackForces(Base):
    __tablename__ = 'BarbarianAttackForces'

    AttackForceType: Mapped[str] = mapped_column(Text, primary_key=True)
    NumMeleeUnits: Mapped[int] = mapped_column(Integer, nullable=False, server_default=text('0'))
    NumRangeUnits: Mapped[int] = mapped_column(Integer, nullable=False, server_default=text('0'))
    NumSiegeUnits: Mapped[int] = mapped_column(Integer, nullable=False, server_default=text('0'))
    NumSupportUnits: Mapped[int] = mapped_column(Integer, nullable=False, server_default=text('0'))
    RaidingForce: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=text('0'))
    SpawnRate: Mapped[int] = mapped_column(Integer, nullable=False, server_default=text('2'))
    MaxTargetDifficulty: Mapped[Optional[str]] = mapped_column(ForeignKey('Difficulties.DifficultyType', ondelete='CASCADE', onupdate='CASCADE'))
    MeleeTag: Mapped[Optional[str]] = mapped_column(Text)
    MinTargetDifficulty: Mapped[Optional[str]] = mapped_column(ForeignKey('Difficulties.DifficultyType', ondelete='CASCADE', onupdate='CASCADE'))
    RangeTag: Mapped[Optional[str]] = mapped_column(Text)
    SiegeTag: Mapped[Optional[str]] = mapped_column(Text)
    SupportTag: Mapped[Optional[str]] = mapped_column(Text)

    Difficulties_: Mapped[Optional['Difficulties']] = relationship('Difficulties', foreign_keys=[MaxTargetDifficulty], back_populates='BarbarianAttackForces')
    Difficulties1: Mapped[Optional['Difficulties']] = relationship('Difficulties', foreign_keys=[MinTargetDifficulty], back_populates='BarbarianAttackForces_')
    BarbarianTribeForces: Mapped[list['BarbarianTribeForces']] = relationship('BarbarianTribeForces', back_populates='BarbarianAttackForces_')


t_Biome_ValidTerrains = Table(
    'Biome_ValidTerrains', Base.metadata,
    Column('BiomeType', ForeignKey('Biomes.BiomeType', ondelete='CASCADE', onupdate='CASCADE'), primary_key=True),
    Column('TerrainType', ForeignKey('Terrains.TerrainType', ondelete='CASCADE', onupdate='CASCADE'), primary_key=True)
)


t_CityExpansionValidTerrains = Table(
    'CityExpansionValidTerrains', Base.metadata,
    Column('CityExpansionType', ForeignKey('CityExpansionTypes.CityExpansionType', ondelete='CASCADE', onupdate='CASCADE'), primary_key=True),
    Column('TerrainType', ForeignKey('Terrains.TerrainType', ondelete='CASCADE', onupdate='CASCADE'), primary_key=True)
)


class CityStateBonuses(Base):
    __tablename__ = 'CityStateBonuses'

    CityStateBonusType: Mapped[str] = mapped_column(Text, primary_key=True)
    CityStateType: Mapped[str] = mapped_column(ForeignKey('CityStateTypes.CityStateType', ondelete='CASCADE', onupdate='CASCADE'), nullable=False)
    Description: Mapped[str] = mapped_column(Text, nullable=False)
    Name: Mapped[str] = mapped_column(Text, nullable=False)
    Shareable: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=text('0'))

    CityStateTypes_: Mapped['CityStateTypes'] = relationship('CityStateTypes', back_populates='CityStateBonuses')
    CityStateBonusModifiers: Mapped[list['CityStateBonusModifiers']] = relationship('CityStateBonusModifiers', back_populates='CityStateBonuses_')


class CivilopediaPageLayoutChapters(Base):
    __tablename__ = 'CivilopediaPageLayoutChapters'

    ChapterID: Mapped[str] = mapped_column(Text, primary_key=True)
    PageLayoutID: Mapped[str] = mapped_column(ForeignKey('CivilopediaPageLayouts.PageLayoutID', ondelete='CASCADE', onupdate='CASCADE'), primary_key=True)
    SortIndex: Mapped[int] = mapped_column(Integer, nullable=False, server_default=text('0'))
    Header: Mapped[Optional[str]] = mapped_column(Text)

    CivilopediaPageLayouts_: Mapped['CivilopediaPageLayouts'] = relationship('CivilopediaPageLayouts', back_populates='CivilopediaPageLayoutChapters')


class CivilopediaPages(Base):
    __tablename__ = 'CivilopediaPages'

    PageID: Mapped[str] = mapped_column(Text, primary_key=True)
    SectionID: Mapped[str] = mapped_column(Text, primary_key=True)
    Name: Mapped[str] = mapped_column(Text, nullable=False)
    PageLayoutID: Mapped[str] = mapped_column(ForeignKey('CivilopediaPageLayouts.PageLayoutID', ondelete='CASCADE', onupdate='CASCADE'), nullable=False)
    SortIndex: Mapped[int] = mapped_column(Integer, nullable=False, server_default=text('0'))
    PageGroupID: Mapped[Optional[str]] = mapped_column(Text)
    TextKeyPrefix: Mapped[Optional[str]] = mapped_column(Text)

    CivilopediaPageLayouts_: Mapped['CivilopediaPageLayouts'] = relationship('CivilopediaPageLayouts', back_populates='CivilopediaPages')


class DiscoverySiftingImprovements(Base):
    __tablename__ = 'DiscoverySiftingImprovements'

    QueueType: Mapped[str] = mapped_column(Text, primary_key=True)
    Activation: Mapped[str] = mapped_column(ForeignKey('DiscoveryStory_Activations.Type', ondelete='CASCADE', onupdate='CASCADE'), nullable=False)
    ConstructibleType: Mapped[str] = mapped_column(Text, nullable=False)

    DiscoveryStory_Activations: Mapped['DiscoveryStoryActivations'] = relationship('DiscoveryStoryActivations', back_populates='DiscoverySiftingImprovements')


class DiscoveryStoryYieldRewards(Base):
    __tablename__ = 'DiscoveryStory_Yield_Rewards'

    Age: Mapped[str] = mapped_column(ForeignKey('Ages.AgeType', ondelete='CASCADE', onupdate='CASCADE'), primary_key=True)
    Type: Mapped[str] = mapped_column(Text, primary_key=True)
    DiplomacyYieldValue: Mapped[Optional[int]] = mapped_column(Integer)
    FoodYieldValue: Mapped[Optional[int]] = mapped_column(Integer)
    GoldYieldValue: Mapped[Optional[int]] = mapped_column(Integer)
    HappinessYieldValue: Mapped[Optional[int]] = mapped_column(Integer)
    ProductionYieldValue: Mapped[Optional[int]] = mapped_column(Integer)
    ProgressionYieldValue: Mapped[Optional[int]] = mapped_column(Integer)

    Ages_: Mapped['Ages'] = relationship('Ages', back_populates='DiscoveryStory_Yield_Rewards')


t_EmbarkationValidTerrains = Table(
    'EmbarkationValidTerrains', Base.metadata,
    Column('EmbarkationType', ForeignKey('UnitEmbarkationTypes.EmbarkationType', ondelete='CASCADE', onupdate='CASCADE'), primary_key=True),
    Column('TerrainType', ForeignKey('Terrains.TerrainType', ondelete='CASCADE', onupdate='CASCADE'), primary_key=True)
)


class GameModifiers(Base):
    __tablename__ = 'GameModifiers'

    ModifierId: Mapped[str] = mapped_column(Text, primary_key=True)
    Age: Mapped[Optional[str]] = mapped_column(ForeignKey('Ages.AgeType', ondelete='CASCADE', onupdate='CASCADE'), primary_key=True, nullable=True)

    Ages_: Mapped[Optional['Ages']] = relationship('Ages', back_populates='GameModifiers')


class GameSpeedScalings(Base):
    __tablename__ = 'GameSpeed_Scalings'

    GameSpeedScalingType: Mapped[str] = mapped_column(Text, primary_key=True)
    DefaultCostMultiplier: Mapped[int] = mapped_column(Integer, nullable=False, server_default=text('100'))
    GameSpeedType: Mapped[str] = mapped_column(ForeignKey('GameSpeeds.GameSpeedType', ondelete='CASCADE', onupdate='CASCADE'), nullable=False)
    ScalingType: Mapped[str] = mapped_column(Text, nullable=False)

    GameSpeeds_: Mapped['GameSpeeds'] = relationship('GameSpeeds', back_populates='GameSpeed_Scalings')
    GameSpeed_Durations: Mapped[list['GameSpeedDurations']] = relationship('GameSpeedDurations', back_populates='GameSpeed_Scalings')


class GameSpeedTurns(Base):
    __tablename__ = 'GameSpeed_Turns'

    GameSpeedType: Mapped[str] = mapped_column(ForeignKey('GameSpeeds.GameSpeedType', ondelete='CASCADE', onupdate='CASCADE'), primary_key=True)
    MonthIncrement: Mapped[int] = mapped_column(Integer, primary_key=True)
    TurnsPerIncrement: Mapped[int] = mapped_column(Integer, primary_key=True)
    Age: Mapped[str] = mapped_column(ForeignKey('Ages.AgeType', ondelete='CASCADE', onupdate='CASCADE'), nullable=False)

    Ages_: Mapped['Ages'] = relationship('Ages', back_populates='GameSpeed_Turns')
    GameSpeeds_: Mapped['GameSpeeds'] = relationship('GameSpeeds', back_populates='GameSpeed_Turns')


class GoldenAgeModifiers(Base):
    __tablename__ = 'GoldenAgeModifiers'

    GoldenAgeType: Mapped[str] = mapped_column(ForeignKey('GoldenAges.GoldenAgeType', ondelete='CASCADE', onupdate='CASCADE'), primary_key=True)
    ModifierID: Mapped[str] = mapped_column(Text, primary_key=True)

    GoldenAges_: Mapped['GoldenAges'] = relationship('GoldenAges', back_populates='GoldenAgeModifiers')


t_Government_ValidGoldenAges = Table(
    'Government_ValidGoldenAges', Base.metadata,
    Column('GoldenAgeType', ForeignKey('GoldenAges.GoldenAgeType', ondelete='CASCADE', onupdate='CASCADE'), primary_key=True),
    Column('GovernmentType', ForeignKey('Governments.GovernmentType', ondelete='CASCADE', onupdate='CASCADE'), primary_key=True)
)


class GreatWorkObjectTypes(Base):
    __tablename__ = 'GreatWorkObjectTypes'

    GreatWorkObjectType: Mapped[str] = mapped_column(Text, primary_key=True)
    IconString: Mapped[str] = mapped_column(Text, nullable=False)
    Name: Mapped[str] = mapped_column(Text, nullable=False)
    PseudoYieldType: Mapped[str] = mapped_column(ForeignKey('PseudoYields.PseudoYieldType', ondelete='CASCADE', onupdate='CASCADE'), nullable=False)
    Value: Mapped[int] = mapped_column(Integer, nullable=False)

    PseudoYields_: Mapped['PseudoYields'] = relationship('PseudoYields', back_populates='GreatWorkObjectTypes')
    GreatWorkSlotTypes_: Mapped[list['GreatWorkSlotTypes']] = relationship('GreatWorkSlotTypes', secondary='GreatWork_ValidSubTypes', back_populates='GreatWorkObjectTypes')
    GoodyHutSubTypes: Mapped[list['GoodyHutSubTypes']] = relationship('GoodyHutSubTypes', back_populates='GreatWorkObjectTypes_')
    GreatPersonIndividuals: Mapped[list['GreatPersonIndividuals']] = relationship('GreatPersonIndividuals', back_populates='GreatWorkObjectTypes_')
    GreatWorks: Mapped[list['GreatWorks']] = relationship('GreatWorks', back_populates='GreatWorkObjectTypes_')


class LegacyPaths(Base):
    __tablename__ = 'LegacyPaths'

    LegacyPathType: Mapped[str] = mapped_column(Text, primary_key=True)
    Age: Mapped[str] = mapped_column(ForeignKey('Ages.AgeType', ondelete='CASCADE', onupdate='CASCADE'), nullable=False)
    EnabledByDefault: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=text('1'))
    LegacyPathClassType: Mapped[str] = mapped_column(ForeignKey('LegacyPathClasses.LegacyPathClassType', ondelete='CASCADE', onupdate='CASCADE'), nullable=False)
    Name: Mapped[str] = mapped_column(Text, nullable=False)
    Description: Mapped[Optional[str]] = mapped_column(Text)

    Ages_: Mapped['Ages'] = relationship('Ages', back_populates='LegacyPaths')
    LegacyPathClasses_: Mapped['LegacyPathClasses'] = relationship('LegacyPathClasses', back_populates='LegacyPaths')
    AgeProgressionMilestones: Mapped[list['AgeProgressionMilestones']] = relationship('AgeProgressionMilestones', back_populates='LegacyPaths_')
    Strategies: Mapped[list['Strategies']] = relationship('Strategies', back_populates='LegacyPaths_')
    ResourceClassApplicableLegacyPaths: Mapped[list['ResourceClassApplicableLegacyPaths']] = relationship('ResourceClassApplicableLegacyPaths', back_populates='LegacyPaths_')


class LoadingInfoAges(Base):
    __tablename__ = 'LoadingInfo_Ages'

    AgeType: Mapped[str] = mapped_column(ForeignKey('Ages.AgeType', ondelete='CASCADE', onupdate='CASCADE'), primary_key=True)
    AgeHeaderTextOverride: Mapped[Optional[str]] = mapped_column(Text)
    AgeIntroText: Mapped[Optional[str]] = mapped_column(Text)
    AgeNameTextOverride: Mapped[Optional[str]] = mapped_column(Text)
    AgeOutroText: Mapped[Optional[str]] = mapped_column(Text)
    CivilizationTypeOverride: Mapped[Optional[str]] = mapped_column(Text)
    LeaderTypeOverride: Mapped[Optional[str]] = mapped_column(Text)


class MapIslandBehavior(Base):
    __tablename__ = 'MapIslandBehavior'

    MapType: Mapped[str] = mapped_column(Text, primary_key=True)
    AgeType: Mapped[str] = mapped_column(ForeignKey('Ages.AgeType', ondelete='SET DEFAULT', onupdate='SET DEFAULT'), nullable=False)
    ResourceClassType: Mapped[str] = mapped_column(Text, nullable=False)

    Ages_: Mapped['Ages'] = relationship('Ages', back_populates='MapIslandBehavior')


class MapReligions(Base):
    __tablename__ = 'Map_Religions'

    MapSizeType: Mapped[str] = mapped_column(ForeignKey('Maps.MapSizeType', ondelete='CASCADE', onupdate='CASCADE'), primary_key=True)
    MaxWorldInstances: Mapped[int] = mapped_column(Integer, nullable=False)


class Modifiers(Base):
    __tablename__ = 'Modifiers'

    ModifierId: Mapped[str] = mapped_column(Text, primary_key=True)
    ModifierType: Mapped[str] = mapped_column(Text, nullable=False)
    NewOnly: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=text('0'))
    Permanent: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=text('0'))
    RunOnce: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=text('0'))
    OwnerRequirementSetId: Mapped[Optional[str]] = mapped_column(ForeignKey('RequirementSets.RequirementSetId', ondelete='CASCADE', onupdate='CASCADE'))
    OwnerStackLimit: Mapped[Optional[int]] = mapped_column(Integer)
    SubjectRequirementSetId: Mapped[Optional[str]] = mapped_column(ForeignKey('RequirementSets.RequirementSetId', ondelete='CASCADE', onupdate='CASCADE'))
    SubjectStackLimit: Mapped[Optional[int]] = mapped_column(Integer)

    Governments_: Mapped[list['Governments']] = relationship('Governments', secondary='GovernmentModifiers', back_populates='Modifiers')
    Mementos_: Mapped[list['Mementos']] = relationship('Mementos', secondary='MementoModifiers', back_populates='Modifiers')
    RequirementSets_: Mapped[Optional['RequirementSets']] = relationship('RequirementSets', foreign_keys=[OwnerRequirementSetId], back_populates='Modifiers')
    RequirementSets1: Mapped[Optional['RequirementSets']] = relationship('RequirementSets', foreign_keys=[SubjectRequirementSetId], back_populates='Modifiers_')
    Traits: Mapped[list['Traits']] = relationship('Traits', secondary='TraitModifiers', back_populates='Modifiers_')
    UnitPromotions: Mapped[list['UnitPromotions']] = relationship('UnitPromotions', secondary='UnitPromotionModifiers', back_populates='Modifiers_')
    Traditions: Mapped[list['Traditions']] = relationship('Traditions', secondary='TraditionModifiers', back_populates='Modifiers_')
    UnitAbilities: Mapped[list['UnitAbilities']] = relationship('UnitAbilities', secondary='UnitAbilityModifiers', back_populates='Modifiers_')
    ModifierArguments: Mapped[list['ModifierArguments']] = relationship('ModifierArguments', back_populates='Modifiers_')
    ModifierStrings: Mapped[list['ModifierStrings']] = relationship('ModifierStrings', back_populates='Modifiers_')
    EnvoysInActionModifiers: Mapped[list['EnvoysInActionModifiers']] = relationship('EnvoysInActionModifiers', back_populates='Modifiers_')
    EnterStageModifiers: Mapped[list['EnterStageModifiers']] = relationship('EnterStageModifiers', back_populates='Modifiers_')
    EnvoysInStageModifiers: Mapped[list['EnvoysInStageModifiers']] = relationship('EnvoysInStageModifiers', back_populates='Modifiers_')


class NamedRiverCivilizations(Base):
    __tablename__ = 'NamedRiverCivilizations'

    CivilizationType: Mapped[str] = mapped_column(Text, primary_key=True)
    NamedRiverType: Mapped[str] = mapped_column(ForeignKey('NamedRivers.NamedRiverType', ondelete='CASCADE', onupdate='CASCADE'), primary_key=True)

    NamedRivers_: Mapped['NamedRivers'] = relationship('NamedRivers', back_populates='NamedRiverCivilizations')


class NamedVolcanoCivilizations(Base):
    __tablename__ = 'NamedVolcanoCivilizations'

    CivilizationType: Mapped[str] = mapped_column(Text, primary_key=True)
    NamedVolcanoType: Mapped[str] = mapped_column(ForeignKey('NamedVolcanoes.NamedVolcanoType', ondelete='CASCADE', onupdate='CASCADE'), primary_key=True)

    NamedVolcanoes_: Mapped['NamedVolcanoes'] = relationship('NamedVolcanoes', back_populates='NamedVolcanoCivilizations')


class NarrativeStoryYieldRewards(Base):
    __tablename__ = 'NarrativeStory_Yield_Rewards'

    Age: Mapped[str] = mapped_column(ForeignKey('Ages.AgeType', ondelete='CASCADE', onupdate='CASCADE'), primary_key=True)
    Type: Mapped[str] = mapped_column(Text, primary_key=True)
    DiplomacyYieldValue: Mapped[Optional[int]] = mapped_column(Integer)
    MaintenanceYieldValue: Mapped[Optional[int]] = mapped_column(Integer)
    ProgressionYieldValue: Mapped[Optional[int]] = mapped_column(Integer)

    Ages_: Mapped['Ages'] = relationship('Ages', back_populates='NarrativeStory_Yield_Rewards')


class NodeDefinitions(Base):
    __tablename__ = 'NodeDefinitions'

    NodeType: Mapped[str] = mapped_column(Text, primary_key=True)
    Description: Mapped[str] = mapped_column(Text, nullable=False)
    NodeId: Mapped[int] = mapped_column(Integer, nullable=False, server_default=text('0'))
    ShapeId: Mapped[int] = mapped_column(ForeignKey('ShapeDefinitions.ShapeId', ondelete='CASCADE', onupdate='CASCADE'), nullable=False)

    ShapeDefinitions_: Mapped['ShapeDefinitions'] = relationship('ShapeDefinitions', back_populates='NodeDefinitions')
    BehaviorTreeNodes: Mapped[list['BehaviorTreeNodes']] = relationship('BehaviorTreeNodes', back_populates='NodeDefinitions_')
    NodeDataDefinitions: Mapped[list['NodeDataDefinitions']] = relationship('NodeDataDefinitions', back_populates='NodeDefinitions_')


class ProgressionTreeNodes(Base):
    __tablename__ = 'ProgressionTreeNodes'

    ProgressionTreeNodeType: Mapped[str] = mapped_column(Text, primary_key=True)
    CanBoost: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=text('1'))
    CanSteal: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=text('1'))
    Cost: Mapped[int] = mapped_column(Integer, nullable=False)
    Name: Mapped[str] = mapped_column(Text, nullable=False, server_default=text('""'))
    ProgressionTree: Mapped[str] = mapped_column(ForeignKey('ProgressionTrees.ProgressionTreeType', ondelete='CASCADE', onupdate='CASCADE'), nullable=False)
    Repeatable: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=text('0'))
    RepeatableCostProgressionModel: Mapped[str] = mapped_column(Text, nullable=False, server_default=text('"NO_PROGRESSION_MODEL"'))
    RepeatableCostProgressionParam1: Mapped[int] = mapped_column(Integer, nullable=False, server_default=text('0'))
    StartingUnlockDepth: Mapped[int] = mapped_column(Integer, nullable=False, server_default=text('-1'))
    Description: Mapped[Optional[str]] = mapped_column(Text)
    IconString: Mapped[Optional[str]] = mapped_column(Text)
    UILayoutColumn: Mapped[Optional[int]] = mapped_column(Integer)
    UILayoutRow: Mapped[Optional[int]] = mapped_column(Integer)

    AdvisoryClasses_: Mapped[list['AdvisoryClasses']] = relationship('AdvisoryClasses', secondary='ProgressionTree_Advisories', back_populates='ProgressionTreeNodes')
    ProgressionTrees_: Mapped['ProgressionTrees'] = relationship('ProgressionTrees', back_populates='ProgressionTreeNodes')
    ProgressionTreeNodes: Mapped[list['ProgressionTreeNodes']] = relationship('ProgressionTreeNodes', secondary='ProgressionTreePrereqs', primaryjoin=lambda: ProgressionTreeNodes.ProgressionTreeNodeType == t_ProgressionTreePrereqs.c.Node, secondaryjoin=lambda: ProgressionTreeNodes.ProgressionTreeNodeType == t_ProgressionTreePrereqs.c.PrereqNode, back_populates='ProgressionTreeNodes_')
    ProgressionTreeNodes_: Mapped[list['ProgressionTreeNodes']] = relationship('ProgressionTreeNodes', secondary='ProgressionTreePrereqs', primaryjoin=lambda: ProgressionTreeNodes.ProgressionTreeNodeType == t_ProgressionTreePrereqs.c.PrereqNode, secondaryjoin=lambda: ProgressionTreeNodes.ProgressionTreeNodeType == t_ProgressionTreePrereqs.c.Node, back_populates='ProgressionTreeNodes')
    Traits: Mapped[list['Traits']] = relationship('Traits', secondary='ProgressionTreeNodeTraits', back_populates='ProgressionTreeNodes_')
    Ideologies: Mapped[list['Ideologies']] = relationship('Ideologies', back_populates='ProgressionTreeNodes_')
    ProgressionTreeNodeUnlocks: Mapped[list['ProgressionTreeNodeUnlocks']] = relationship('ProgressionTreeNodeUnlocks', back_populates='ProgressionTreeNodes_')
    GameSystemPrereqs: Mapped[list['GameSystemPrereqs']] = relationship('GameSystemPrereqs', back_populates='ProgressionTreeNodes_')


class RequirementArguments(Base):
    __tablename__ = 'RequirementArguments'

    Name: Mapped[str] = mapped_column(Text, primary_key=True)
    RequirementId: Mapped[str] = mapped_column(ForeignKey('Requirements.RequirementId', ondelete='CASCADE', onupdate='CASCADE'), primary_key=True)
    Value: Mapped[str] = mapped_column(Text, nullable=False)
    Extra: Mapped[Optional[str]] = mapped_column(Text)
    SecondExtra: Mapped[Optional[str]] = mapped_column(Text)
    Type: Mapped[Optional[str]] = mapped_column(Text)

    Requirements_: Mapped['Requirements'] = relationship('Requirements', back_populates='RequirementArguments')


t_RequirementSetRequirements = Table(
    'RequirementSetRequirements', Base.metadata,
    Column('RequirementId', ForeignKey('Requirements.RequirementId', ondelete='CASCADE', onupdate='CASCADE'), primary_key=True),
    Column('RequirementSetId', ForeignKey('RequirementSets.RequirementSetId', ondelete='CASCADE', onupdate='CASCADE'), primary_key=True)
)


class RequirementStrings(Base):
    __tablename__ = 'RequirementStrings'

    Context: Mapped[str] = mapped_column(Text, primary_key=True)
    RequirementId: Mapped[str] = mapped_column(ForeignKey('Requirements.RequirementId', ondelete='CASCADE', onupdate='CASCADE'), primary_key=True)
    Text_: Mapped[str] = mapped_column('Text', Text, nullable=False)

    Requirements_: Mapped['Requirements'] = relationship('Requirements', back_populates='RequirementStrings')


class ScoringLineItems(Base):
    __tablename__ = 'ScoringLineItems'

    LineItemType: Mapped[str] = mapped_column(Text, primary_key=True)
    Buildings: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=text('0'))
    Category: Mapped[str] = mapped_column(ForeignKey('ScoringCategories.CategoryType', ondelete='CASCADE', onupdate='CASCADE'), nullable=False)
    Cities: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=text('0'))
    Converted: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=text('0'))
    Districts: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=text('0'))
    GoldPerTurn: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=text('0'))
    GreatPeople: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=text('0'))
    Multiplier: Mapped[float] = mapped_column(REAL, nullable=False, server_default=text('1'))
    Name: Mapped[str] = mapped_column(Text, nullable=False)
    Pillage: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=text('0'))
    Population: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=text('0'))
    Religion: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=text('0'))
    ScaleByCost: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=text('0'))
    ScoringScenario1: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=text('0'))
    ScoringScenario2: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=text('0'))
    ScoringScenario3: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=text('0'))
    Techs: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=text('0'))
    TieBreakerPriority: Mapped[int] = mapped_column(Integer, nullable=False)
    Wonders: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=text('0'))

    ScoringCategories_: Mapped['ScoringCategories'] = relationship('ScoringCategories', back_populates='ScoringLineItems')


class StandardHandicaps(Base):
    __tablename__ = 'StandardHandicaps'

    DifficultyType: Mapped[str] = mapped_column(ForeignKey('Difficulties.DifficultyType', ondelete='CASCADE', onupdate='CASCADE'), primary_key=True)
    HandicapSystemType: Mapped[str] = mapped_column(ForeignKey('HandicapSystems.HandicapSystemType', ondelete='CASCADE', onupdate='CASCADE'), primary_key=True)
    HandicapLevel: Mapped[int] = mapped_column(Integer, nullable=False)

    Difficulties_: Mapped['Difficulties'] = relationship('Difficulties', back_populates='StandardHandicaps')
    HandicapSystems_: Mapped['HandicapSystems'] = relationship('HandicapSystems', back_populates='StandardHandicaps')


t_StartingGovernments = Table(
    'StartingGovernments', Base.metadata,
    Column('AgeType', ForeignKey('Ages.AgeType', ondelete='CASCADE', onupdate='CASCADE'), primary_key=True),
    Column('GovernmentType', ForeignKey('Governments.GovernmentType', ondelete='CASCADE', onupdate='CASCADE'), primary_key=True, server_default=text('"NO_GOVERNMENT"'))
)


class Tags(Base):
    __tablename__ = 'Tags'

    Tag: Mapped[str] = mapped_column(Text, primary_key=True)
    Category: Mapped[str] = mapped_column(ForeignKey('TagCategories.Category', ondelete='CASCADE', onupdate='CASCADE'), nullable=False)
    Hash: Mapped[int] = mapped_column(Integer, nullable=False, server_default=text('0'))

    TagCategories_: Mapped['TagCategories'] = relationship('TagCategories', back_populates='Tags')
    DiplomacyActions: Mapped[list['DiplomacyActions']] = relationship('DiplomacyActions', secondary='UnitDiplomacyAction_ValidUnits', back_populates='Tags_')
    OpTeamRequirements: Mapped[list['OpTeamRequirements']] = relationship('OpTeamRequirements', back_populates='Tags_')
    TypeTags: Mapped[list['TypeTags']] = relationship('TypeTags', back_populates='Tags_')
    UnitDiplomacyAction_Targets: Mapped[list['UnitDiplomacyActionTargets']] = relationship('UnitDiplomacyActionTargets', back_populates='Tags_')


class TradeYields(Base):
    __tablename__ = 'TradeYields'

    Domain: Mapped[str] = mapped_column(Text, primary_key=True, server_default=text('"NO_DOMAIN"'))
    ResourceCount: Mapped[int] = mapped_column(Integer, primary_key=True)
    Amount: Mapped[int] = mapped_column(Integer, nullable=False)
    YieldType: Mapped[str] = mapped_column(ForeignKey('Yields.YieldType', ondelete='CASCADE', onupdate='CASCADE'), nullable=False)

    Yields_: Mapped['Yields'] = relationship('Yields', back_populates='TradeYields')


class TreeData(Base):
    __tablename__ = 'TreeData'

    UniqueId: Mapped[int] = mapped_column(Integer, primary_key=True)
    DefnId: Mapped[int] = mapped_column(Integer, nullable=False)
    NodeId: Mapped[int] = mapped_column(Integer, nullable=False)
    TreeName: Mapped[str] = mapped_column(ForeignKey('BehaviorTrees.TreeName', ondelete='CASCADE', onupdate='CASCADE'), nullable=False)
    DefaultData: Mapped[Optional[str]] = mapped_column(Text)
    ParentTag: Mapped[Optional[str]] = mapped_column(Text)
    Tag: Mapped[Optional[str]] = mapped_column(Text)

    BehaviorTrees_: Mapped['BehaviorTrees'] = relationship('BehaviorTrees', back_populates='TreeData')


class TribeCombatTags(Base):
    __tablename__ = 'TribeCombatTags'

    CombatTag: Mapped[str] = mapped_column(Text, primary_key=True)
    TribeTagSet: Mapped[str] = mapped_column(ForeignKey('TribeTagSets.TribeTagName', ondelete='CASCADE', onupdate='CASCADE'), primary_key=True)

    TribeTagSets_: Mapped['TribeTagSets'] = relationship('TribeTagSets', back_populates='TribeCombatTags')


class TribeForbiddenCombatTags(Base):
    __tablename__ = 'TribeForbiddenCombatTags'

    CombatTag: Mapped[str] = mapped_column(Text, primary_key=True)
    TribeTagSet: Mapped[str] = mapped_column(ForeignKey('TribeTagSets.TribeTagName', ondelete='CASCADE', onupdate='CASCADE'), primary_key=True)

    TribeTagSets_: Mapped['TribeTagSets'] = relationship('TribeTagSets', back_populates='TribeForbiddenCombatTags')


class TribeRequiredCombatTags(Base):
    __tablename__ = 'TribeRequiredCombatTags'

    CombatTag: Mapped[str] = mapped_column(Text, primary_key=True)
    TribeTagSet: Mapped[str] = mapped_column(ForeignKey('TribeTagSets.TribeTagName', ondelete='CASCADE', onupdate='CASCADE'), primary_key=True)

    TribeTagSets_: Mapped['TribeTagSets'] = relationship('TribeTagSets', back_populates='TribeRequiredCombatTags')


class TriggeredBehaviorTrees(Base):
    __tablename__ = 'TriggeredBehaviorTrees'

    TriggerType: Mapped[str] = mapped_column(Text, primary_key=True)
    AIEvent: Mapped[str] = mapped_column(ForeignKey('AiEvents.EventType', ondelete='CASCADE', onupdate='CASCADE'), nullable=False)
    Priority: Mapped[int] = mapped_column(Integer, nullable=False, server_default=text('0'))
    TreeName: Mapped[str] = mapped_column(ForeignKey('BehaviorTrees.TreeName', ondelete='CASCADE', onupdate='CASCADE'), nullable=False)
    OperationName: Mapped[Optional[str]] = mapped_column(Text)

    AiEvents_: Mapped['AiEvents'] = relationship('AiEvents', back_populates='TriggeredBehaviorTrees')
    BehaviorTrees_: Mapped['BehaviorTrees'] = relationship('BehaviorTrees', back_populates='TriggeredBehaviorTrees')


class TurnPhases(Base):
    __tablename__ = 'TurnPhases'

    ActiveSegmentType: Mapped[str] = mapped_column(ForeignKey('TurnSegments.TurnSegmentType', ondelete='CASCADE', onupdate='CASCADE'), nullable=False)
    PhaseOrder: Mapped[int] = mapped_column(Integer, nullable=False)
    TurnMode: Mapped[str] = mapped_column(Text, nullable=False)
    TurnPhaseType: Mapped[str] = mapped_column(Text, nullable=False)
    ID: Mapped[Optional[int]] = mapped_column(Integer, primary_key=True)
    InactiveSegmentType: Mapped[Optional[str]] = mapped_column(ForeignKey('TurnSegments.TurnSegmentType', ondelete='CASCADE', onupdate='CASCADE'))

    TurnSegments_: Mapped['TurnSegments'] = relationship('TurnSegments', foreign_keys=[ActiveSegmentType], back_populates='TurnPhases')
    TurnSegments1: Mapped[Optional['TurnSegments']] = relationship('TurnSegments', foreign_keys=[InactiveSegmentType], back_populates='TurnPhases_')


class UnitCommands(Base):
    __tablename__ = 'UnitCommands'

    CommandType: Mapped[str] = mapped_column(Text, primary_key=True)
    HoldCycling: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=text('0'))
    Icon: Mapped[str] = mapped_column(Text, nullable=False)
    MaxAge: Mapped[int] = mapped_column(Integer, nullable=False, server_default=text('-1'))
    Name: Mapped[str] = mapped_column(Text, nullable=False)
    RequiresAbility: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=text('0'))
    ShowActivationPlots: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=text('0'))
    VisibleInUI: Mapped[bool] = mapped_column(Boolean, nullable=False)
    CategoryInUI: Mapped[Optional[str]] = mapped_column(Text)
    Description: Mapped[Optional[str]] = mapped_column(Text)
    DisabledHelp: Mapped[Optional[str]] = mapped_column(Text)
    Help: Mapped[Optional[str]] = mapped_column(Text)
    HotkeyId: Mapped[Optional[str]] = mapped_column(Text)
    InterfaceMode: Mapped[Optional[str]] = mapped_column(ForeignKey('InterfaceModes.InterfaceModeType', ondelete='CASCADE', onupdate='CASCADE'))
    PriorityInUI: Mapped[Optional[int]] = mapped_column(Integer)
    Sound: Mapped[Optional[str]] = mapped_column(Text)

    InterfaceModes_: Mapped[Optional['InterfaceModes']] = relationship('InterfaceModes', back_populates='UnitCommands')
    UnitAbilities: Mapped[list['UnitAbilities']] = relationship('UnitAbilities', back_populates='UnitCommands_')
    AIUnitPrioritizedActions: Mapped[list['AIUnitPrioritizedActions']] = relationship('AIUnitPrioritizedActions', back_populates='UnitCommands_')


class Victories(Base):
    __tablename__ = 'Victories'

    VictoryType: Mapped[str] = mapped_column(Text, primary_key=True)
    EnabledByDefault: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=text('1'))
    LegacyPathClassType: Mapped[str] = mapped_column(Text, nullable=False, server_default=text('"NO_LEGACY_PATH_CLASS"'))
    Name: Mapped[str] = mapped_column(Text, nullable=False)
    RequirementSetId: Mapped[str] = mapped_column(ForeignKey('RequirementSets.RequirementSetId', ondelete='CASCADE', onupdate='CASCADE'), nullable=False)
    RequiresMultipleTeams: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=text('0'))
    VictoryClassType: Mapped[str] = mapped_column(ForeignKey('VictoryClasses.VictoryClassType', ondelete='CASCADE', onupdate='CASCADE'), nullable=False)
    Description: Mapped[Optional[str]] = mapped_column(Text)

    RequirementSets_: Mapped['RequirementSets'] = relationship('RequirementSets', back_populates='Victories')
    VictoryClasses_: Mapped['VictoryClasses'] = relationship('VictoryClasses', back_populates='Victories')
    Units: Mapped[list['Units']] = relationship('Units', back_populates='Victories_')


class VisArtPlotEffectModifiers(Base):
    __tablename__ = 'VisArt_PlotEffectModifiers'

    PlotEffectSource: Mapped[str] = mapped_column(Text, primary_key=True)
    PlotEffectType: Mapped[str] = mapped_column(ForeignKey('PlotEffects.PlotEffectType', ondelete='CASCADE', onupdate='CASCADE'), primary_key=True)
    AddDelay: Mapped[Optional[float]] = mapped_column(REAL)

    PlotEffects_: Mapped['PlotEffects'] = relationship('PlotEffects', back_populates='VisArt_PlotEffectModifiers')


class WorkerYields(Base):
    __tablename__ = 'WorkerYields'

    YieldType: Mapped[str] = mapped_column(ForeignKey('Yields.YieldType', ondelete='CASCADE', onupdate='CASCADE'), primary_key=True)
    Amount: Mapped[int] = mapped_column(Integer, nullable=False)


class AdvancedStartAIModifiers(Base):
    __tablename__ = 'AdvancedStartAIModifiers'

    AiList: Mapped[str] = mapped_column(Text, primary_key=True)
    CardID: Mapped[str] = mapped_column(ForeignKey('AdvancedStartCards.CardID', ondelete='CASCADE', onupdate='CASCADE'), primary_key=True)

    AdvancedStartCards_: Mapped['AdvancedStartCards'] = relationship('AdvancedStartCards', back_populates='AdvancedStartAIModifiers')


t_AdvancedStartDeckCardEntries = Table(
    'AdvancedStartDeckCardEntries', Base.metadata,
    Column('CardID', ForeignKey('AdvancedStartCards.CardID', ondelete='CASCADE', onupdate='CASCADE'), nullable=False),
    Column('DeckID', ForeignKey('AdvancedStartDecks.DeckID', ondelete='CASCADE', onupdate='CASCADE'), nullable=False)
)


class AgeCrisisEvents(Base):
    __tablename__ = 'AgeCrisisEvents'

    AgeCrisisEventType: Mapped[str] = mapped_column(Text, primary_key=True)
    Age: Mapped[str] = mapped_column(ForeignKey('Ages.AgeType', ondelete='CASCADE', onupdate='CASCADE'), nullable=False)
    AgeCrisisType: Mapped[str] = mapped_column(ForeignKey('AgeCrises.AgeCrisisType', ondelete='CASCADE', onupdate='CASCADE'), nullable=False)
    NarrativeStoryType: Mapped[str] = mapped_column(Text, nullable=False)

    Ages_: Mapped['Ages'] = relationship('Ages', back_populates='AgeCrisisEvents')
    AgeCrises_: Mapped['AgeCrises'] = relationship('AgeCrises', back_populates='AgeCrisisEvents')
    AgeCrisisStages: Mapped[list['AgeCrisisStages']] = relationship('AgeCrisisStages', back_populates='AgeCrisisEvents_')


t_AgeProgressionDarkAgeRewardInfos = Table(
    'AgeProgressionDarkAgeRewardInfos', Base.metadata,
    Column('Description', Text),
    Column('Icon', Text),
    Column('LegacyPathType', ForeignKey('LegacyPaths.LegacyPathType', ondelete='CASCADE', onupdate='CASCADE'), nullable=False),
    Column('Name', Text)
)


class AgeProgressionEventMapSizeOverrides(Base):
    __tablename__ = 'AgeProgressionEventMapSizeOverrides'

    AgeProgressionEventType: Mapped[str] = mapped_column(ForeignKey('AgeProgressionEvents.AgeProgressionEventType', ondelete='CASCADE', onupdate='CASCADE'), primary_key=True)
    MapSizeType: Mapped[str] = mapped_column(ForeignKey('Maps.MapSizeType', ondelete='CASCADE', onupdate='CASCADE'), primary_key=True)
    Points: Mapped[int] = mapped_column(Integer, nullable=False, server_default=text('0'))

    AgeProgressionEvents_: Mapped['AgeProgressionEvents'] = relationship('AgeProgressionEvents', back_populates='AgeProgressionEventMapSizeOverrides')
    Maps_: Mapped['Maps'] = relationship('Maps', back_populates='AgeProgressionEventMapSizeOverrides')


class AgeProgressionMilestones(Base):
    __tablename__ = 'AgeProgressionMilestones'

    AgeProgressionMilestoneType: Mapped[str] = mapped_column(ForeignKey('Types.Type', ondelete='CASCADE', onupdate='CASCADE'), primary_key=True)
    AgeProgressionEventType: Mapped[str] = mapped_column(ForeignKey('AgeProgressionEvents.AgeProgressionEventType', ondelete='CASCADE', onupdate='CASCADE'), nullable=False)
    FinalMilestone: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=text('0'))
    LegacyPathType: Mapped[str] = mapped_column(ForeignKey('LegacyPaths.LegacyPathType', ondelete='CASCADE', onupdate='CASCADE'), nullable=False)
    RequiredPathPoints: Mapped[int] = mapped_column(Integer, nullable=False, server_default=text('0'))

    AgeProgressionEvents_: Mapped['AgeProgressionEvents'] = relationship('AgeProgressionEvents', back_populates='AgeProgressionMilestones')
    LegacyPaths_: Mapped['LegacyPaths'] = relationship('LegacyPaths', back_populates='AgeProgressionMilestones')
    AgeProgressionMilestoneRewards: Mapped[list['AgeProgressionMilestoneRewards']] = relationship('AgeProgressionMilestoneRewards', back_populates='AgeProgressionMilestones_')


class AiOperationTeams(Base):
    __tablename__ = 'AiOperationTeams'

    OperationName: Mapped[str] = mapped_column(ForeignKey('AiOperationDefs.OperationName', ondelete='CASCADE', onupdate='CASCADE'), primary_key=True)
    TeamName: Mapped[str] = mapped_column(ForeignKey('AiTeams.TeamName', ondelete='CASCADE', onupdate='CASCADE'), primary_key=True)
    InitialStrengthAdvantage: Mapped[float] = mapped_column(REAL, nullable=False, server_default=text('0'))
    MaxUnits: Mapped[int] = mapped_column(Integer, nullable=False, server_default=text('-1'))
    MinUnits: Mapped[int] = mapped_column(Integer, nullable=False, server_default=text('1'))
    OngoingStrengthAdvantage: Mapped[float] = mapped_column(REAL, nullable=False, server_default=text('0'))
    SafeRallyPoint: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=text('0'))
    Condition: Mapped[Optional[str]] = mapped_column(Text)

    AiOperationDefs_: Mapped['AiOperationDefs'] = relationship('AiOperationDefs', back_populates='AiOperationTeams')
    AiTeams_: Mapped['AiTeams'] = relationship('AiTeams', back_populates='AiOperationTeams')


class AllowedOperations(Base):
    __tablename__ = 'AllowedOperations'

    ListType: Mapped[str] = mapped_column(ForeignKey('AiOperationLists.ListType', ondelete='CASCADE', onupdate='CASCADE'), primary_key=True)
    OperationDef: Mapped[str] = mapped_column(ForeignKey('AiOperationDefs.OperationName', ondelete='CASCADE', onupdate='CASCADE'), primary_key=True)
    RemoveRef: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=text('0'))

    AiOperationLists_: Mapped['AiOperationLists'] = relationship('AiOperationLists', back_populates='AllowedOperations')
    AiOperationDefs_: Mapped['AiOperationDefs'] = relationship('AiOperationDefs', back_populates='AllowedOperations')


class BehaviorTreeNodes(Base):
    __tablename__ = 'BehaviorTreeNodes'

    PrimaryKey: Mapped[int] = mapped_column(Integer, primary_key=True)
    JumpTo: Mapped[int] = mapped_column(Integer, nullable=False, server_default=text('0'))
    NodeId: Mapped[int] = mapped_column(Integer, nullable=False)
    NodeType: Mapped[str] = mapped_column(ForeignKey('NodeDefinitions.NodeType', ondelete='CASCADE', onupdate='CASCADE'), nullable=False)
    TreeName: Mapped[str] = mapped_column(ForeignKey('BehaviorTrees.TreeName', ondelete='CASCADE', onupdate='CASCADE'), nullable=False)

    NodeDefinitions_: Mapped['NodeDefinitions'] = relationship('NodeDefinitions', back_populates='BehaviorTreeNodes')
    BehaviorTrees_: Mapped['BehaviorTrees'] = relationship('BehaviorTrees', back_populates='BehaviorTreeNodes')


class Beliefs(Base):
    __tablename__ = 'Beliefs'

    BeliefType: Mapped[str] = mapped_column(ForeignKey('Types.Type', ondelete='CASCADE', onupdate='CASCADE'), primary_key=True)
    AISelectionBin: Mapped[int] = mapped_column(Integer, nullable=False)
    BeliefClassType: Mapped[str] = mapped_column(ForeignKey('BeliefClasses.BeliefClassType', ondelete='CASCADE', onupdate='CASCADE'), nullable=False)
    Description: Mapped[str] = mapped_column(Text, nullable=False)
    Name: Mapped[str] = mapped_column(Text, nullable=False)
    Shareable: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=text('0'))

    BeliefClasses_: Mapped['BeliefClasses'] = relationship('BeliefClasses', back_populates='Beliefs')
    AiListTypes_: Mapped[list['AiListTypes']] = relationship('AiListTypes', secondary='Belief_Priorities', back_populates='Beliefs')
    BeliefModifiers: Mapped[list['BeliefModifiers']] = relationship('BeliefModifiers', back_populates='Beliefs_')


class BoostHandlers(Base):
    __tablename__ = 'BoostHandlers'

    HandlerId: Mapped[Optional[str]] = mapped_column(Text, primary_key=True)
    BehaviorTree: Mapped[Optional[str]] = mapped_column(ForeignKey('BehaviorTrees.TreeName', ondelete='CASCADE', onupdate='CASCADE'))
    OperationName: Mapped[Optional[str]] = mapped_column(ForeignKey('AiOperationDefs.OperationName', ondelete='CASCADE', onupdate='CASCADE'))
    Script: Mapped[Optional[str]] = mapped_column(Text)
    UniquenessTag: Mapped[Optional[str]] = mapped_column(Text)
    WinnowFunction: Mapped[Optional[str]] = mapped_column(Text)

    BehaviorTrees_: Mapped[Optional['BehaviorTrees']] = relationship('BehaviorTrees', back_populates='BoostHandlers')
    AiOperationDefs_: Mapped[Optional['AiOperationDefs']] = relationship('AiOperationDefs', back_populates='BoostHandlers')


class CityStateBonusModifiers(Base):
    __tablename__ = 'CityStateBonusModifiers'

    CityStateBonusType: Mapped[str] = mapped_column(ForeignKey('CityStateBonuses.CityStateBonusType', ondelete='CASCADE', onupdate='CASCADE'), primary_key=True)
    ModifierID: Mapped[str] = mapped_column(Text, primary_key=True)

    CityStateBonuses_: Mapped['CityStateBonuses'] = relationship('CityStateBonuses', back_populates='CityStateBonusModifiers')


class Civilizations(Base):
    __tablename__ = 'Civilizations'

    CivilizationType: Mapped[str] = mapped_column(ForeignKey('Types.Type', ondelete='CASCADE', onupdate='CASCADE'), primary_key=True)
    Adjective: Mapped[str] = mapped_column(Text, nullable=False)
    AITargetCityPercentage: Mapped[int] = mapped_column(Integer, nullable=False, server_default=text('50'))
    CapitalName: Mapped[str] = mapped_column(Text, nullable=False)
    FullName: Mapped[str] = mapped_column(Text, nullable=False)
    Name: Mapped[str] = mapped_column(Text, nullable=False)
    RandomCityNameDepth: Mapped[int] = mapped_column(Integer, nullable=False, server_default=text('1'))
    StartingCivilizationLevelType: Mapped[str] = mapped_column(ForeignKey('CivilizationLevels.CivilizationLevelType', ondelete='SET DEFAULT', onupdate='CASCADE'), nullable=False)
    Description: Mapped[Optional[str]] = mapped_column(Text)
    UniqueCultureProgressionTree: Mapped[Optional[str]] = mapped_column(ForeignKey('ProgressionTrees.ProgressionTreeType', ondelete='SET DEFAULT', onupdate='CASCADE'))

    CivilizationLevels_: Mapped['CivilizationLevels'] = relationship('CivilizationLevels', back_populates='Civilizations')
    ProgressionTrees_: Mapped[Optional['ProgressionTrees']] = relationship('ProgressionTrees', back_populates='Civilizations')
    Traits: Mapped[list['Traits']] = relationship('Traits', secondary='CivilizationTraits', back_populates='Civilizations_')
    Resources: Mapped[list['Resources']] = relationship('Resources', secondary='Resource_RequiredCivs', back_populates='Civilizations_')
    CityNames: Mapped[list['CityNames']] = relationship('CityNames', back_populates='Civilizations_')
    CivilizationCitizenNames: Mapped[list['CivilizationCitizenNames']] = relationship('CivilizationCitizenNames', back_populates='Civilizations_')
    CivilizationInfo: Mapped[list['CivilizationInfo']] = relationship('CivilizationInfo', back_populates='Civilizations_')
    FavoredReligions: Mapped[list['FavoredReligions']] = relationship('FavoredReligions', back_populates='Civilizations_')
    LeaderCivPriorities: Mapped[list['LeaderCivPriorities']] = relationship('LeaderCivPriorities', back_populates='Civilizations_')
    MetaprogressionModifiers: Mapped[list['MetaprogressionModifiers']] = relationship('MetaprogressionModifiers', back_populates='Civilizations_')
    StartBiasAdjacentToCoasts: Mapped[list['StartBiasAdjacentToCoasts']] = relationship('StartBiasAdjacentToCoasts', back_populates='Civilizations_')
    StartBiasBiomes: Mapped[list['StartBiasBiomes']] = relationship('StartBiasBiomes', back_populates='Civilizations_')
    StartBiasFeatureClasses: Mapped[list['StartBiasFeatureClasses']] = relationship('StartBiasFeatureClasses', back_populates='Civilizations_')
    StartBiasLakes: Mapped[list['StartBiasLakes']] = relationship('StartBiasLakes', back_populates='Civilizations_')
    StartBiasNaturalWonders: Mapped[list['StartBiasNaturalWonders']] = relationship('StartBiasNaturalWonders', back_populates='Civilizations_')
    StartBiasRivers: Mapped[list['StartBiasRivers']] = relationship('StartBiasRivers', back_populates='Civilizations_')
    StartBiasTerrains: Mapped[list['StartBiasTerrains']] = relationship('StartBiasTerrains', back_populates='Civilizations_')
    VisArt_CivilizationBuildingCultures: Mapped[list['VisArtCivilizationBuildingCultures']] = relationship('VisArtCivilizationBuildingCultures', back_populates='Civilizations_')
    VisArt_CivilizationUnitCultures: Mapped[list['VisArtCivilizationUnitCultures']] = relationship('VisArtCivilizationUnitCultures', back_populates='Civilizations_')
    StartBiasResources: Mapped[list['StartBiasResources']] = relationship('StartBiasResources', back_populates='Civilizations_')


class Defeats(Base):
    __tablename__ = 'Defeats'

    DefeatType: Mapped[str] = mapped_column(ForeignKey('Types.Type', ondelete='CASCADE', onupdate='CASCADE'), primary_key=True)
    AllowAgeTransition: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=text('0'))
    AllowOneMoreTurn: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=text('0'))
    Blurb: Mapped[str] = mapped_column(Text, nullable=False)
    EnabledByDefault: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=text('1'))
    Global: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=text('0'))
    Name: Mapped[str] = mapped_column(Text, nullable=False)
    RequirementSetId: Mapped[Optional[str]] = mapped_column(ForeignKey('RequirementSets.RequirementSetId', ondelete='CASCADE', onupdate='CASCADE'))

    RequirementSets_: Mapped[Optional['RequirementSets']] = relationship('RequirementSets', back_populates='Defeats')


class DiplomacyActionGroupSubtypes(Base):
    __tablename__ = 'DiplomacyActionGroupSubtypes'

    DiplomacyActionGroupSubtypeType: Mapped[str] = mapped_column(ForeignKey('Types.Type', ondelete='CASCADE', onupdate='CASCADE'), primary_key=True)
    Name: Mapped[str] = mapped_column(Text, nullable=False)


class DiplomacyActionGroups(Base):
    __tablename__ = 'DiplomacyActionGroups'

    DiplomacyActionGroupType: Mapped[str] = mapped_column(ForeignKey('Types.Type', ondelete='CASCADE', onupdate='CASCADE'), primary_key=True)
    Name: Mapped[str] = mapped_column(Text, nullable=False)

    DiplomaticProjects_UI_Data: Mapped[list['DiplomaticProjectsUIData']] = relationship('DiplomaticProjectsUIData', back_populates='DiplomacyActionGroups_')


class DiplomacyActionTags(Base):
    __tablename__ = 'DiplomacyActionTags'

    DiplomacyActionTagType: Mapped[str] = mapped_column(ForeignKey('Types.Type', ondelete='CASCADE', onupdate='CASCADE'), primary_key=True)
    Name: Mapped[str] = mapped_column(Text, nullable=False)


class DiplomacyActions(Base):
    __tablename__ = 'DiplomacyActions'

    DiplomacyActionType: Mapped[str] = mapped_column(ForeignKey('Types.Type', ondelete='CASCADE', onupdate='CASCADE'), primary_key=True)
    AllyOnly: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=text('0'))
    AlwaysNotifyTarget: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=text('0'))
    BaseDuration: Mapped[int] = mapped_column(Integer, nullable=False, server_default=text('5'))
    BaseTokenCost: Mapped[int] = mapped_column(Integer, nullable=False, server_default=text('0'))
    BlocksTargetProject: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=text('0'))
    CancelPenalty: Mapped[int] = mapped_column(Integer, nullable=False, server_default=text('0'))
    Description: Mapped[str] = mapped_column(Text, nullable=False)
    EnvoysInfluenceProgress: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=text('0'))
    IsMutualSupport: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=text('0'))
    MaxThirdPartySupport: Mapped[int] = mapped_column(Integer, nullable=False, server_default=text('0'))
    Momentum: Mapped[int] = mapped_column(Integer, nullable=False, server_default=text('0'))
    MustStartFromUnit: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=text('0'))
    Name: Mapped[str] = mapped_column(Text, nullable=False)
    NegativeProgressAllowed: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=text('0'))
    NumTimesPerPlayer: Mapped[int] = mapped_column(Integer, nullable=False, server_default=text('-1'))
    Opposable: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=text('1'))
    Opposed: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=text('0'))
    RandomInitialProgress: Mapped[int] = mapped_column(Integer, nullable=False, server_default=text('0'))
    RejectionRefundsInfluence: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=text('0'))
    RelativeZero: Mapped[int] = mapped_column(Integer, nullable=False, server_default=text('0'))
    RequiresUnlock: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=text('0'))
    RevealChance: Mapped[int] = mapped_column(Integer, nullable=False, server_default=text('100'))
    RevealPenaltyRelationshipHit: Mapped[int] = mapped_column(Integer, nullable=False, server_default=text('0'))
    SingleInstanceProject: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=text('1'))
    SuccessChance: Mapped[int] = mapped_column(Integer, nullable=False, server_default=text('100'))
    Supportable: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=text('1'))
    SupportFavors: Mapped[int] = mapped_column(Integer, nullable=False, server_default=text('100'))
    SupportWindow: Mapped[int] = mapped_column(Integer, nullable=False, server_default=text('-1'))
    Symmetrical: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=text('0'))
    TargetFavors: Mapped[int] = mapped_column(Integer, nullable=False, server_default=text('0'))
    TargetFavorsFreq: Mapped[int] = mapped_column(Integer, nullable=False, server_default=text('0'))
    UIIconPath: Mapped[str] = mapped_column(Text, nullable=False, server_default=text('"fs://game/dip_endeavors"'))
    UnsupportPenalty: Mapped[int] = mapped_column(Integer, nullable=False, server_default=text('0'))
    WarOnly: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=text('0'))
    ChangeSupportMsg: Mapped[Optional[str]] = mapped_column(Text)
    DiplomacyActionTag: Mapped[Optional[str]] = mapped_column(ForeignKey('Types.Type', ondelete='CASCADE', onupdate='CASCADE'))
    OpposeDesc: Mapped[Optional[str]] = mapped_column(Text)
    OpposeRemovedDesc: Mapped[Optional[str]] = mapped_column(Text)
    RequestString: Mapped[Optional[str]] = mapped_column(Text)
    SupportDesc: Mapped[Optional[str]] = mapped_column(Text)
    SupportRemovedDesc: Mapped[Optional[str]] = mapped_column(Text)

    Types_: Mapped[Optional['Types']] = relationship('Types', foreign_keys=[DiplomacyActionTag], back_populates='DiplomacyActions')
    Types1: Mapped[list['Types']] = relationship('Types', secondary='DiplomaticActionValidTokens', back_populates='DiplomacyActions_')
    Tags_: Mapped[list['Tags']] = relationship('Tags', secondary='UnitDiplomacyAction_ValidUnits', back_populates='DiplomacyActions')
    DiplomaticActionResponseModifiers: Mapped[list['DiplomaticActionResponseModifiers']] = relationship('DiplomaticActionResponseModifiers', back_populates='DiplomacyActions_')
    DiplomaticActionResponses: Mapped[list['DiplomaticActionResponses']] = relationship('DiplomaticActionResponses', back_populates='DiplomacyActions_')
    DiplomaticActionStages: Mapped[list['DiplomaticActionStages']] = relationship('DiplomaticActionStages', back_populates='DiplomacyActions_')
    EnvoysInActionModifiers: Mapped[list['EnvoysInActionModifiers']] = relationship('EnvoysInActionModifiers', back_populates='DiplomacyActions_')
    UnitDiplomacyAction_Targets: Mapped[list['UnitDiplomacyActionTargets']] = relationship('UnitDiplomacyActionTargets', back_populates='DiplomacyActions_')


class DiplomacyAgendaAmountTypes(Base):
    __tablename__ = 'DiplomacyAgendaAmountTypes'

    DiplomacyAgendaAmountType: Mapped[str] = mapped_column(ForeignKey('Types.Type', ondelete='CASCADE', onupdate='CASCADE'), primary_key=True)
    Amount: Mapped[int] = mapped_column(Integer, nullable=False, server_default=text('0'))
    Name: Mapped[str] = mapped_column(Text, nullable=False)


class DiplomacyAgendaAwardToTypes(Base):
    __tablename__ = 'DiplomacyAgendaAwardToTypes'

    DiplomacyAgendaAwardToType: Mapped[str] = mapped_column(ForeignKey('Types.Type', ondelete='CASCADE', onupdate='CASCADE'), primary_key=True)
    Name: Mapped[str] = mapped_column(Text, nullable=False)


class DiplomacyAgendaWeightingTypes(Base):
    __tablename__ = 'DiplomacyAgendaWeightingTypes'

    DiplomacyAgendaWeightingType: Mapped[str] = mapped_column(ForeignKey('Types.Type', ondelete='CASCADE', onupdate='CASCADE'), primary_key=True)
    Name: Mapped[str] = mapped_column(Text, nullable=False)


class DiplomacyBasicModifierValueTypes(Base):
    __tablename__ = 'DiplomacyBasicModifierValueTypes'

    DiplomacyBasicModifierValueType: Mapped[str] = mapped_column(ForeignKey('Types.Type', ondelete='CASCADE', onupdate='CASCADE'), primary_key=True)
    Name: Mapped[str] = mapped_column(Text, nullable=False)


class DiplomacyFavorGrievanceEventGroups(Base):
    __tablename__ = 'DiplomacyFavorGrievanceEventGroups'

    DiplomacyFavorGrievanceEventGroupType: Mapped[str] = mapped_column(ForeignKey('Types.Type', ondelete='CASCADE', onupdate='CASCADE'), primary_key=True)
    Name: Mapped[str] = mapped_column(Text, nullable=False)


class DiplomacyFavorsGrievancesEventsData(Base):
    __tablename__ = 'DiplomacyFavorsGrievancesEventsData'

    DiplomacyFavorGrievanceEventType: Mapped[str] = mapped_column(Text, primary_key=True)
    Amount: Mapped[int] = mapped_column(Integer, nullable=False, server_default=text('0'))
    DiplomacyFavorGrievanceEventGroup: Mapped[str] = mapped_column(ForeignKey('Types.Type', ondelete='CASCADE', onupdate='CASCADE'), nullable=False)
    InfAward: Mapped[int] = mapped_column(Integer, nullable=False, server_default=text('0'))
    InfAwardPerPopulation: Mapped[int] = mapped_column(Integer, nullable=False, server_default=text('0'))
    Name: Mapped[str] = mapped_column(Text, nullable=False)
    Range: Mapped[int] = mapped_column(Integer, nullable=False, server_default=text('-1'))
    TeamPropagation: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=text('1'))

    Types_: Mapped['Types'] = relationship('Types', back_populates='DiplomacyFavorsGrievancesEventsData')


class DiplomacyModifierTargetTypes(Base):
    __tablename__ = 'DiplomacyModifierTargetTypes'

    DiplomacyModifierTargetType: Mapped[str] = mapped_column(ForeignKey('Types.Type', ondelete='CASCADE', onupdate='CASCADE'), primary_key=True)
    Name: Mapped[str] = mapped_column(Text, nullable=False)


class DiplomaticActionInfluenceCosts(Base):
    __tablename__ = 'DiplomaticActionInfluenceCosts'

    DiplomacyActionType: Mapped[str] = mapped_column(ForeignKey('Types.Type', ondelete='CASCADE', onupdate='CASCADE'), primary_key=True)
    InfCostFriendly: Mapped[int] = mapped_column(Integer, nullable=False, server_default=text('-1'))
    InfCostHelpful: Mapped[int] = mapped_column(Integer, nullable=False, server_default=text('-1'))
    InfCostHostile: Mapped[int] = mapped_column(Integer, nullable=False, server_default=text('-1'))
    InfCostNeutral: Mapped[int] = mapped_column(Integer, nullable=False, server_default=text('-1'))
    InfCostNoRelationship: Mapped[int] = mapped_column(Integer, nullable=False, server_default=text('-1'))
    InfCostPerTurn: Mapped[int] = mapped_column(Integer, nullable=False, server_default=text('0'))
    InfCostSupportIncreaseFlat: Mapped[int] = mapped_column(Integer, nullable=False, server_default=text('0'))
    InfCostSupportIncreasePercent: Mapped[int] = mapped_column(Integer, nullable=False, server_default=text('0'))
    InfCostUnfriendly: Mapped[int] = mapped_column(Integer, nullable=False, server_default=text('-1'))
    PenaltyInfCostDuration: Mapped[int] = mapped_column(Integer, nullable=False, server_default=text('0'))
    PenaltyInfCostPerTurn: Mapped[int] = mapped_column(Integer, nullable=False, server_default=text('0'))


class DiplomaticFirstMeetResponses(Base):
    __tablename__ = 'DiplomaticFirstMeetResponses'

    DiplomaticFirstMeetResponseType: Mapped[str] = mapped_column(ForeignKey('Types.Type', ondelete='CASCADE', onupdate='CASCADE'), primary_key=True)
    Amount: Mapped[int] = mapped_column(Integer, nullable=False, server_default=text('0'))
    InfCost: Mapped[int] = mapped_column(Integer, nullable=False, server_default=text('0'))
    Name: Mapped[str] = mapped_column(Text, nullable=False)
    ShowCapitalRadius: Mapped[int] = mapped_column(Integer, nullable=False, server_default=text('1'))
    ShowCapitalRange: Mapped[int] = mapped_column(Integer, nullable=False, server_default=text('10'))
    ShowCapitals: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=text('0'))


class DiplomaticResponses(Base):
    __tablename__ = 'DiplomaticResponses'

    DiplomaticResponseType: Mapped[str] = mapped_column(ForeignKey('Types.Type', ondelete='CASCADE', onupdate='CASCADE'), primary_key=True)
    Name: Mapped[str] = mapped_column(Text, nullable=False)


class Districts(Base):
    __tablename__ = 'Districts'

    DistrictType: Mapped[str] = mapped_column(ForeignKey('Types.Type', ondelete='CASCADE', onupdate='CASCADE'), primary_key=True)
    AirSlots: Mapped[int] = mapped_column(Integer, nullable=False, server_default=text('0'))
    AutoPlace: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=text('0'))
    AutoRemove: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=text('0'))
    CanAttack: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=text('0'))
    CaptureRemovesBuildings: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=text('0'))
    CaptureRemovesCityDefenses: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=text('0'))
    CaptureRemovesDistrict: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=text('0'))
    CitizenSlots: Mapped[int] = mapped_column(Integer, nullable=False, server_default=text('0'))
    CityStrengthModifier: Mapped[int] = mapped_column(Integer, nullable=False, server_default=text('0'))
    DistrictClass: Mapped[str] = mapped_column(Text, nullable=False)
    FreeEmbark: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=text('0'))
    HitPoints: Mapped[int] = mapped_column(Integer, nullable=False, server_default=text('0'))
    Maintenance: Mapped[int] = mapped_column(Integer, nullable=False, server_default=text('0'))
    MaxConstructibles: Mapped[int] = mapped_column(Integer, nullable=False, server_default=text('1'))
    MilitaryDomain: Mapped[str] = mapped_column(Text, nullable=False, server_default=text('"NO_DOMAIN"'))
    Name: Mapped[str] = mapped_column(Text, nullable=False)
    NatureYields: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=text('0'))
    OnePerCity: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=text('0'))
    OverwritePreviousAge: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=text('0'))
    ResourceBlocks: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=text('0'))
    Roads: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=text('0'))
    TravelTime: Mapped[int] = mapped_column(Integer, nullable=False, server_default=text('-1'))
    UrbanCoreType: Mapped[str] = mapped_column(Text, nullable=False)
    Water: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=text('0'))
    Workable: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=text('0'))
    Description: Mapped[Optional[str]] = mapped_column(Text)

    Traits: Mapped[list['Traits']] = relationship('Traits', secondary='ExcludedDistricts', back_populates='Districts_')
    Features: Mapped[list['Features']] = relationship('Features', secondary='District_RemovedFeatures', back_populates='Districts_')
    Constructibles: Mapped[list['Constructibles']] = relationship('Constructibles', back_populates='Districts_')
    Constructibles_: Mapped[list['Constructibles']] = relationship('Constructibles', secondary='Constructible_ValidDistricts', back_populates='Districts1')
    UnitOperations: Mapped[list['UnitOperations']] = relationship('UnitOperations', back_populates='Districts_')
    Adjacency_YieldChanges: Mapped[list['AdjacencyYieldChanges']] = relationship('AdjacencyYieldChanges', back_populates='Districts_')
    Warehouse_YieldChanges: Mapped[list['WarehouseYieldChanges']] = relationship('WarehouseYieldChanges', back_populates='Districts_')
    AdvancedStartUnits: Mapped[list['AdvancedStartUnits']] = relationship('AdvancedStartUnits', back_populates='Districts_')
    Boosts: Mapped[list['Boosts']] = relationship('Boosts', back_populates='Districts_')
    GreatPersonIndividuals: Mapped[list['GreatPersonIndividuals']] = relationship('GreatPersonIndividuals', back_populates='Districts_')


class DynamicModifiers(Base):
    __tablename__ = 'DynamicModifiers'

    ModifierType: Mapped[str] = mapped_column(ForeignKey('Types.Type', ondelete='CASCADE', onupdate='CASCADE'), primary_key=True)
    CollectionType: Mapped[str] = mapped_column(ForeignKey('Types.Type', ondelete='CASCADE', onupdate='CASCADE'), nullable=False)
    EffectType: Mapped[str] = mapped_column(ForeignKey('Types.Type', ondelete='CASCADE', onupdate='CASCADE'), nullable=False)

    Types_: Mapped['Types'] = relationship('Types', foreign_keys=[CollectionType], back_populates='DynamicModifiers')
    Types1: Mapped['Types'] = relationship('Types', foreign_keys=[EffectType], back_populates='DynamicModifiers_')


class EventClasses(Base):
    __tablename__ = 'EventClasses'

    EventClass: Mapped[str] = mapped_column(ForeignKey('Types.Type', ondelete='CASCADE', onupdate='CASCADE'), primary_key=True)


class FeatureClasses(Base):
    __tablename__ = 'FeatureClasses'

    FeatureClassType: Mapped[str] = mapped_column(ForeignKey('Types.Type', ondelete='CASCADE', onupdate='CASCADE'), primary_key=True)
    Adjective: Mapped[str] = mapped_column(Text, nullable=False)
    Description: Mapped[str] = mapped_column(Text, nullable=False)
    Name: Mapped[str] = mapped_column(Text, nullable=False)

    Constructibles: Mapped[list['Constructibles']] = relationship('Constructibles', secondary='Constructible_RequiredFeatureClasses', back_populates='FeatureClasses_')
    Features: Mapped[list['Features']] = relationship('Features', back_populates='FeatureClasses_')
    StartBiasFeatureClasses: Mapped[list['StartBiasFeatureClasses']] = relationship('StartBiasFeatureClasses', back_populates='FeatureClasses_')
    Warehouse_YieldChanges: Mapped[list['WarehouseYieldChanges']] = relationship('WarehouseYieldChanges', back_populates='FeatureClasses_')


class GameCapabilities(Base):
    __tablename__ = 'GameCapabilities'

    GameCapability: Mapped[Optional[str]] = mapped_column(ForeignKey('Types.Type', ondelete='CASCADE', onupdate='CASCADE'), primary_key=True)

    GameCapabilityDependencies: Mapped[list['GameCapabilityDependencies']] = relationship('GameCapabilityDependencies', foreign_keys='[GameCapabilityDependencies.DependsOnCapability]', back_populates='GameCapabilities_')
    GameCapabilityDependencies_: Mapped[list['GameCapabilityDependencies']] = relationship('GameCapabilityDependencies', foreign_keys='[GameCapabilityDependencies.GameCapability]', back_populates='GameCapabilities1')


class GameEffects(Base):
    __tablename__ = 'GameEffects'

    Type: Mapped[Optional[str]] = mapped_column(ForeignKey('Types.Type', ondelete='CASCADE', onupdate='CASCADE'), primary_key=True)
    ContextInterfaces: Mapped[Optional[str]] = mapped_column(Text)
    Description: Mapped[Optional[str]] = mapped_column(Text)
    GameCapabilities_: Mapped[Optional[str]] = mapped_column('GameCapabilities', Text)
    SubjectInterfaces: Mapped[Optional[str]] = mapped_column(Text)
    SupportsRemove: Mapped[Optional[bool]] = mapped_column(Boolean)

    GameEffectArguments: Mapped[list['GameEffectArguments']] = relationship('GameEffectArguments', back_populates='GameEffects_')


class GameSpeedDurations(Base):
    __tablename__ = 'GameSpeed_Durations'

    GameSpeedScalingType: Mapped[str] = mapped_column(ForeignKey('GameSpeed_Scalings.GameSpeedScalingType', ondelete='CASCADE', onupdate='CASCADE'), primary_key=True)
    NumberOfTurnsOnStandard: Mapped[int] = mapped_column(Integer, primary_key=True)
    NumberOfTurnsScaled: Mapped[int] = mapped_column(Integer, nullable=False)

    GameSpeed_Scalings: Mapped['GameSpeedScalings'] = relationship('GameSpeedScalings', back_populates='GameSpeed_Durations')


class GoodyHutSubTypes(Base):
    __tablename__ = 'GoodyHutSubTypes'

    SubTypeGoodyHut: Mapped[str] = mapped_column(Text, primary_key=True)
    GoodyHut: Mapped[str] = mapped_column(ForeignKey('GoodyHuts.GoodyHutType', ondelete='CASCADE', onupdate='CASCADE'), nullable=False)
    Heal: Mapped[int] = mapped_column(Integer, nullable=False, server_default=text('0'))
    MinOneCity: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=text('0'))
    ModifierID: Mapped[str] = mapped_column(Text, nullable=False)
    NearestCityNaval: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=text('0'))
    RequiresUnit: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=text('0'))
    Turn: Mapped[int] = mapped_column(Integer, nullable=False, server_default=text('0'))
    UpgradeUnit: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=text('0'))
    Weight: Mapped[int] = mapped_column(Integer, nullable=False)
    Description: Mapped[Optional[str]] = mapped_column(Text)
    RequiresCityGreatWorkObjectType: Mapped[Optional[str]] = mapped_column(ForeignKey('GreatWorkObjectTypes.GreatWorkObjectType', ondelete='CASCADE', onupdate='CASCADE'))

    GoodyHuts_: Mapped['GoodyHuts'] = relationship('GoodyHuts', back_populates='GoodyHutSubTypes')
    GreatWorkObjectTypes_: Mapped[Optional['GreatWorkObjectTypes']] = relationship('GreatWorkObjectTypes', back_populates='GoodyHutSubTypes')


class Gossips(Base):
    __tablename__ = 'Gossips'

    GossipType: Mapped[str] = mapped_column(ForeignKey('Types.Type', ondelete='CASCADE', onupdate='CASCADE'), primary_key=True)
    Message: Mapped[str] = mapped_column(Text, nullable=False)
    Description: Mapped[Optional[str]] = mapped_column(Text)


t_GovernmentAttributes = Table(
    'GovernmentAttributes', Base.metadata,
    Column('AttributeType', ForeignKey('Attributes.AttributeType', ondelete='CASCADE', onupdate='CASCADE'), primary_key=True),
    Column('GovernmentType', ForeignKey('Governments.GovernmentType', ondelete='CASCADE', onupdate='CASCADE'), primary_key=True)
)


t_GovernmentModifiers = Table(
    'GovernmentModifiers', Base.metadata,
    Column('GovernmentType', ForeignKey('Governments.GovernmentType', ondelete='CASCADE', onupdate='CASCADE'), primary_key=True),
    Column('ModifierId', ForeignKey('Modifiers.ModifierId', ondelete='CASCADE', onupdate='CASCADE'), primary_key=True)
)


t_GreatWork_ValidSubTypes = Table(
    'GreatWork_ValidSubTypes', Base.metadata,
    Column('GreatWorkObjectType', ForeignKey('GreatWorkObjectTypes.GreatWorkObjectType', ondelete='CASCADE', onupdate='CASCADE'), primary_key=True),
    Column('GreatWorkSlotType', ForeignKey('GreatWorkSlotTypes.GreatWorkSlotType', ondelete='CASCADE', onupdate='CASCADE'), primary_key=True)
)


class Ideologies(Base):
    __tablename__ = 'Ideologies'

    IdeologyType: Mapped[str] = mapped_column(Text, primary_key=True)
    FirstTreeNode: Mapped[str] = mapped_column(ForeignKey('ProgressionTreeNodes.ProgressionTreeNodeType', ondelete='CASCADE', onupdate='CASCADE'), nullable=False)
    Name: Mapped[str] = mapped_column(Text, nullable=False)
    ProgressionTreeType: Mapped[str] = mapped_column(ForeignKey('ProgressionTrees.ProgressionTreeType', ondelete='CASCADE', onupdate='CASCADE'), nullable=False)
    RivalIdeology: Mapped[Optional[str]] = mapped_column(ForeignKey('Ideologies.IdeologyType', ondelete='CASCADE', onupdate='CASCADE'))

    ProgressionTreeNodes_: Mapped['ProgressionTreeNodes'] = relationship('ProgressionTreeNodes', back_populates='Ideologies')
    ProgressionTrees_: Mapped['ProgressionTrees'] = relationship('ProgressionTrees', back_populates='Ideologies')
    Ideologies: Mapped[Optional['Ideologies']] = relationship('Ideologies', remote_side=[IdeologyType], back_populates='Ideologies_reverse')
    Ideologies_reverse: Mapped[list['Ideologies']] = relationship('Ideologies', remote_side=[RivalIdeology], back_populates='Ideologies')
    IdeologyAdoptionModifiers: Mapped[list['IdeologyAdoptionModifiers']] = relationship('IdeologyAdoptionModifiers', back_populates='Ideologies_')
    IdeologyPriorities: Mapped[list['IdeologyPriorities']] = relationship('IdeologyPriorities', back_populates='Ideologies_')


class Leaders(Base):
    __tablename__ = 'Leaders'

    LeaderType: Mapped[str] = mapped_column(ForeignKey('Types.Type', ondelete='CASCADE', onupdate='CASCADE'), primary_key=True)
    AITargetCityPercentage: Mapped[int] = mapped_column(Integer, nullable=False, server_default=text('50'))
    DiscountRate: Mapped[int] = mapped_column(Integer, nullable=False, server_default=text('0'))
    IsBarbarianLeader: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=text('0'))
    IsIndependentLeader: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=text('0'))
    IsMajorLeader: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=text('0'))
    Name: Mapped[str] = mapped_column(Text, nullable=False)
    BasePersonaType: Mapped[Optional[str]] = mapped_column(Text)
    InheritFrom: Mapped[Optional[str]] = mapped_column(ForeignKey('Leaders.LeaderType', ondelete='SET DEFAULT', onupdate='SET DEFAULT'))
    OperationList: Mapped[Optional[str]] = mapped_column(ForeignKey('AiOperationLists.ListType', ondelete='SET DEFAULT', onupdate='SET DEFAULT'))

    Leaders: Mapped[Optional['Leaders']] = relationship('Leaders', remote_side=[LeaderType], back_populates='Leaders_reverse')
    Leaders_reverse: Mapped[list['Leaders']] = relationship('Leaders', remote_side=[InheritFrom], back_populates='Leaders')
    AiOperationLists_: Mapped[Optional['AiOperationLists']] = relationship('AiOperationLists', back_populates='Leaders')
    Traits: Mapped[list['Traits']] = relationship('Traits', secondary='LeaderTraits', back_populates='Leaders_')
    Resources: Mapped[list['Resources']] = relationship('Resources', secondary='Resource_RequiredLeaders', back_populates='Leaders_')
    CityNames: Mapped[list['CityNames']] = relationship('CityNames', back_populates='Leaders_')
    FavoredReligions: Mapped[list['FavoredReligions']] = relationship('FavoredReligions', back_populates='Leaders_')
    LeaderCivPriorities: Mapped[list['LeaderCivPriorities']] = relationship('LeaderCivPriorities', back_populates='Leaders_')
    LeaderInfo: Mapped[list['LeaderInfo']] = relationship('LeaderInfo', back_populates='Leaders_')
    LegacyLeaderCivPriorities: Mapped[list['LegacyLeaderCivPriorities']] = relationship('LegacyLeaderCivPriorities', back_populates='Leaders_')
    MetaprogressionModifiers: Mapped[list['MetaprogressionModifiers']] = relationship('MetaprogressionModifiers', back_populates='Leaders_')
    StartBiasAdjacentToCoasts: Mapped[list['StartBiasAdjacentToCoasts']] = relationship('StartBiasAdjacentToCoasts', back_populates='Leaders_')
    StartBiasBiomes: Mapped[list['StartBiasBiomes']] = relationship('StartBiasBiomes', back_populates='Leaders_')
    StartBiasFeatureClasses: Mapped[list['StartBiasFeatureClasses']] = relationship('StartBiasFeatureClasses', back_populates='Leaders_')
    StartBiasLakes: Mapped[list['StartBiasLakes']] = relationship('StartBiasLakes', back_populates='Leaders_')
    StartBiasNaturalWonders: Mapped[list['StartBiasNaturalWonders']] = relationship('StartBiasNaturalWonders', back_populates='Leaders_')
    StartBiasRivers: Mapped[list['StartBiasRivers']] = relationship('StartBiasRivers', back_populates='Leaders_')
    StartBiasTerrains: Mapped[list['StartBiasTerrains']] = relationship('StartBiasTerrains', back_populates='Leaders_')
    StartBiasResources: Mapped[list['StartBiasResources']] = relationship('StartBiasResources', back_populates='Leaders_')


class LegacyCivilizations(Base):
    __tablename__ = 'LegacyCivilizations'

    CivilizationType: Mapped[str] = mapped_column(ForeignKey('Types.Type', ondelete='CASCADE', onupdate='CASCADE'), primary_key=True)
    Adjective: Mapped[str] = mapped_column(Text, nullable=False)
    Age: Mapped[str] = mapped_column(ForeignKey('Ages.AgeType', ondelete='CASCADE', onupdate='CASCADE'), nullable=False)
    FullName: Mapped[str] = mapped_column(Text, nullable=False)
    Name: Mapped[str] = mapped_column(Text, nullable=False)

    Ages_: Mapped['Ages'] = relationship('Ages', back_populates='LegacyCivilizations')
    Traits: Mapped[list['Traits']] = relationship('Traits', secondary='LegacyCivilizationTraits', back_populates='LegacyCivilizations_')


t_MementoModifiers = Table(
    'MementoModifiers', Base.metadata,
    Column('MementoType', ForeignKey('Mementos.MementoType', ondelete='CASCADE', onupdate='CASCADE'), primary_key=True),
    Column('ModifierId', ForeignKey('Modifiers.ModifierId', ondelete='CASCADE', onupdate='CASCADE'), primary_key=True)
)


class ModifierArguments(Base):
    __tablename__ = 'ModifierArguments'

    ModifierId: Mapped[str] = mapped_column(ForeignKey('Modifiers.ModifierId', ondelete='CASCADE', onupdate='CASCADE'), primary_key=True)
    Name: Mapped[str] = mapped_column(Text, primary_key=True)
    Value: Mapped[str] = mapped_column(Text, nullable=False)
    Extra: Mapped[Optional[str]] = mapped_column(Text)
    SecondExtra: Mapped[Optional[str]] = mapped_column(Text)
    Type: Mapped[Optional[str]] = mapped_column(Text)

    Modifiers_: Mapped['Modifiers'] = relationship('Modifiers', back_populates='ModifierArguments')


class ModifierStrings(Base):
    __tablename__ = 'ModifierStrings'

    Context: Mapped[str] = mapped_column(Text, primary_key=True)
    ModifierId: Mapped[str] = mapped_column(ForeignKey('Modifiers.ModifierId', ondelete='CASCADE', onupdate='CASCADE'), primary_key=True)
    Text_: Mapped[str] = mapped_column('Text', Text, nullable=False)

    Modifiers_: Mapped['Modifiers'] = relationship('Modifiers', back_populates='ModifierStrings')


class NarrativeStories(Base):
    __tablename__ = 'NarrativeStories'

    NarrativeStoryType: Mapped[str] = mapped_column(ForeignKey('Types.Type', ondelete='CASCADE', onupdate='CASCADE'), primary_key=True)
    Activation: Mapped[str] = mapped_column(ForeignKey('NarrativeStory_Activations.Type', ondelete='CASCADE', onupdate='CASCADE'), nullable=False)
    Cost: Mapped[int] = mapped_column(Integer, nullable=False, server_default=text('0'))
    Crisis: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=text('0'))
    Description: Mapped[str] = mapped_column(Text, nullable=False)
    ForceChoice: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=text('0'))
    ForeignOnly: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=text('0'))
    Hidden: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=text('0'))
    IsQuest: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=text('0'))
    Name: Mapped[str] = mapped_column(Text, nullable=False)
    ReducedScaling: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=text('0'))
    ShowProgress: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=text('0'))
    ActivationRequirementSetId: Mapped[Optional[str]] = mapped_column(Text)
    Age: Mapped[Optional[str]] = mapped_column(Text)
    AllowDuplicates: Mapped[Optional[bool]] = mapped_column(Boolean, server_default=text('0'))
    Completion: Mapped[Optional[str]] = mapped_column(Text)
    CostYield: Mapped[Optional[str]] = mapped_column(ForeignKey('Yields.YieldType', ondelete='CASCADE', onupdate='CASCADE'))
    EndTurn: Mapped[Optional[int]] = mapped_column(Integer)
    FirstOnly: Mapped[Optional[bool]] = mapped_column(Boolean)
    Imperative: Mapped[Optional[str]] = mapped_column(Text)
    Multiplayer: Mapped[Optional[bool]] = mapped_column(Boolean)
    Percentage: Mapped[Optional[int]] = mapped_column(Integer)
    PullQuote: Mapped[Optional[str]] = mapped_column(Text)
    Queue: Mapped[Optional[str]] = mapped_column(ForeignKey('NarrativeStory_Queues.QueueType', ondelete='CASCADE', onupdate='CASCADE'))
    RequirementSetId: Mapped[Optional[str]] = mapped_column(Text)
    ResourceReq: Mapped[Optional[str]] = mapped_column(Text)
    StartEveryone: Mapped[Optional[bool]] = mapped_column(Boolean, server_default=text('0'))
    StoryTitle: Mapped[Optional[str]] = mapped_column(Text)
    Timeout: Mapped[Optional[int]] = mapped_column(Integer)
    UIActivation: Mapped[Optional[str]] = mapped_column(ForeignKey('NarrativeStory_UIActivations.Type', ondelete='CASCADE', onupdate='CASCADE'))

    NarrativeStory_Activations: Mapped['NarrativeStoryActivations'] = relationship('NarrativeStoryActivations', back_populates='NarrativeStories')
    Yields_: Mapped[Optional['Yields']] = relationship('Yields', back_populates='NarrativeStories')
    NarrativeStory_Queues: Mapped[Optional['NarrativeStoryQueues']] = relationship('NarrativeStoryQueues', back_populates='NarrativeStories')
    NarrativeStory_UIActivations: Mapped[Optional['NarrativeStoryUIActivations']] = relationship('NarrativeStoryUIActivations', back_populates='NarrativeStories')
    NarrativeRewardIcons: Mapped[list['NarrativeRewardIcons']] = relationship('NarrativeRewardIcons', back_populates='NarrativeStories_')
    NarrativeStoryOverrides: Mapped[list['NarrativeStoryOverrides']] = relationship('NarrativeStoryOverrides', back_populates='NarrativeStories_')
    NarrativeStory_Links: Mapped[list['NarrativeStoryLinks']] = relationship('NarrativeStoryLinks', back_populates='NarrativeStories_')
    NarrativeStory_Rewards: Mapped[list['NarrativeStoryRewards']] = relationship('NarrativeStoryRewards', back_populates='NarrativeStories_')
    NarrativeStory_TextReplacements: Mapped[list['NarrativeStoryTextReplacements']] = relationship('NarrativeStoryTextReplacements', back_populates='NarrativeStories_')
    NarrativeVariations: Mapped[list['NarrativeVariations']] = relationship('NarrativeVariations', back_populates='NarrativeStories_')


class NodeDataDefinitions(Base):
    __tablename__ = 'NodeDataDefinitions'

    UniqueId: Mapped[int] = mapped_column(Integer, primary_key=True)
    Automatic: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=text('0'))
    DataName: Mapped[str] = mapped_column(Text, nullable=False)
    DataType: Mapped[str] = mapped_column(ForeignKey('DataTypes.TypeName', ondelete='CASCADE', onupdate='CASCADE'), nullable=False)
    DefnId: Mapped[int] = mapped_column(Integer, nullable=False)
    Modified: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=text('0'))
    NodeType: Mapped[str] = mapped_column(ForeignKey('NodeDefinitions.NodeType', ondelete='CASCADE', onupdate='CASCADE'), nullable=False)
    Output: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=text('0'))
    Required: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=text('0'))
    RequiredGroup: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=text('0'))
    Tagged: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=text('0'))
    UserData: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=text('0'))
    EnumList: Mapped[Optional[str]] = mapped_column(Text)

    DataTypes_: Mapped['DataTypes'] = relationship('DataTypes', back_populates='NodeDataDefinitions')
    NodeDefinitions_: Mapped['NodeDefinitions'] = relationship('NodeDefinitions', back_populates='NodeDataDefinitions')


class OpTeamRequirements(Base):
    __tablename__ = 'OpTeamRequirements'

    ClassTag: Mapped[str] = mapped_column(ForeignKey('Tags.Tag', ondelete='CASCADE', onupdate='CASCADE'), primary_key=True)
    TeamName: Mapped[str] = mapped_column(ForeignKey('AiTeams.TeamName', ondelete='CASCADE', onupdate='CASCADE'), primary_key=True)
    MaxPercentage: Mapped[float] = mapped_column(REAL, nullable=False, server_default=text('1'))
    MinPercentage: Mapped[float] = mapped_column(REAL, nullable=False, server_default=text('0'))
    ReconsiderWhilePreparing: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=text('0'))
    AiTypeDependence: Mapped[Optional[str]] = mapped_column(Text)
    MaxNumber: Mapped[Optional[int]] = mapped_column(Integer)
    MinNumber: Mapped[Optional[int]] = mapped_column(Integer)
    Property: Mapped[Optional[str]] = mapped_column(Text)

    Tags_: Mapped['Tags'] = relationship('Tags', back_populates='OpTeamRequirements')
    AiTeams_: Mapped['AiTeams'] = relationship('AiTeams', back_populates='OpTeamRequirements')


t_ProgressionTreePrereqs = Table(
    'ProgressionTreePrereqs', Base.metadata,
    Column('Node', ForeignKey('ProgressionTreeNodes.ProgressionTreeNodeType', ondelete='CASCADE', onupdate='CASCADE'), primary_key=True),
    Column('PrereqNode', ForeignKey('ProgressionTreeNodes.ProgressionTreeNodeType', ondelete='CASCADE', onupdate='CASCADE'), primary_key=True)
)


t_ProgressionTree_Advisories = Table(
    'ProgressionTree_Advisories', Base.metadata,
    Column('AdvisoryClassType', ForeignKey('AdvisoryClasses.AdvisoryClassType', ondelete='CASCADE', onupdate='CASCADE'), primary_key=True),
    Column('ProgressionTreeNodeType', ForeignKey('ProgressionTreeNodes.ProgressionTreeNodeType', ondelete='CASCADE', onupdate='CASCADE'), primary_key=True)
)


class Quests(Base):
    __tablename__ = 'Quests'

    QuestType: Mapped[str] = mapped_column(ForeignKey('Types.Type', ondelete='CASCADE', onupdate='CASCADE'), primary_key=True)
    Description: Mapped[str] = mapped_column(Text, nullable=False)
    IconString: Mapped[str] = mapped_column(Text, nullable=False)
    Name: Mapped[str] = mapped_column(Text, nullable=False)
    Reward: Mapped[str] = mapped_column(Text, nullable=False)
    InstanceDescription: Mapped[Optional[str]] = mapped_column(Text)
    InstanceName: Mapped[Optional[str]] = mapped_column(Text)
    InstanceReward: Mapped[Optional[str]] = mapped_column(Text)


class Religions(Base):
    __tablename__ = 'Religions'

    ReligionType: Mapped[str] = mapped_column(ForeignKey('Types.Type', ondelete='CASCADE', onupdate='CASCADE'), primary_key=True)
    Color: Mapped[str] = mapped_column(Text, nullable=False)
    IconString: Mapped[str] = mapped_column(Text, nullable=False)
    Name: Mapped[str] = mapped_column(Text, nullable=False)
    Pantheon: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=text('0'))
    RequiresCustomName: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=text('0'))

    FavoredReligions: Mapped[list['FavoredReligions']] = relationship('FavoredReligions', back_populates='Religions_')


class ResourceClasses(Base):
    __tablename__ = 'ResourceClasses'

    ResourceClassType: Mapped[str] = mapped_column(ForeignKey('Types.Type', ondelete='CASCADE', onupdate='CASCADE'), primary_key=True)
    Assignable: Mapped[bool] = mapped_column(Boolean, nullable=False)
    Description: Mapped[str] = mapped_column(Text, nullable=False)
    Name: Mapped[str] = mapped_column(Text, nullable=False)

    ResourceClassApplicableLegacyPaths: Mapped[list['ResourceClassApplicableLegacyPaths']] = relationship('ResourceClassApplicableLegacyPaths', back_populates='ResourceClasses_')
    Resources: Mapped[list['Resources']] = relationship('Resources', back_populates='ResourceClasses_')
    GameSystemPrereqs: Mapped[list['GameSystemPrereqs']] = relationship('GameSystemPrereqs', back_populates='ResourceClasses_')


class Strategies(Base):
    __tablename__ = 'Strategies'

    StrategyType: Mapped[str] = mapped_column(Text, primary_key=True)
    CityStrategy: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=text('0'))
    MaxNumConditionsNeeded: Mapped[int] = mapped_column(Integer, nullable=False, server_default=text('1'))
    MinConditionPercentage: Mapped[int] = mapped_column(Integer, nullable=False, server_default=text('25'))
    MinNumConditionsNeeded: Mapped[int] = mapped_column(Integer, nullable=False, server_default=text('1'))
    BehaviorTree: Mapped[Optional[str]] = mapped_column(ForeignKey('BehaviorTrees.TreeName', ondelete='CASCADE', onupdate='CASCADE'))
    CountdownVictoryType: Mapped[Optional[str]] = mapped_column(ForeignKey('VictoryTypes.VictoryType', ondelete='CASCADE', onupdate='CASCADE'))
    LegacyPathType: Mapped[Optional[str]] = mapped_column(ForeignKey('LegacyPaths.LegacyPathType', ondelete='CASCADE', onupdate='CASCADE'))
    SaveGoldForVictory: Mapped[Optional[str]] = mapped_column(Text)
    SaveInfluenceForVictory: Mapped[Optional[str]] = mapped_column(Text)

    AiListTypes_: Mapped[list['AiListTypes']] = relationship('AiListTypes', secondary='Strategy_Priorities', back_populates='Strategies')
    BehaviorTrees_: Mapped[Optional['BehaviorTrees']] = relationship('BehaviorTrees', back_populates='Strategies')
    VictoryTypes_: Mapped[Optional['VictoryTypes']] = relationship('VictoryTypes', back_populates='Strategies')
    LegacyPaths_: Mapped[Optional['LegacyPaths']] = relationship('LegacyPaths', back_populates='Strategies')
    StrategyConditions: Mapped[list['StrategyConditions']] = relationship('StrategyConditions', back_populates='Strategies_')
    Strategy_YieldPriorities: Mapped[list['StrategyYieldPriorities']] = relationship('StrategyYieldPriorities', back_populates='Strategies_')


class Traits(Base):
    __tablename__ = 'Traits'

    TraitType: Mapped[str] = mapped_column(ForeignKey('Types.Type', ondelete='CASCADE', onupdate='CASCADE'), primary_key=True)
    InternalOnly: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=text('0'))
    Description: Mapped[Optional[str]] = mapped_column(Text)
    Name: Mapped[Optional[str]] = mapped_column(Text)

    Modifiers_: Mapped[list['Modifiers']] = relationship('Modifiers', secondary='TraitModifiers', back_populates='Traits')
    ProgressionTreeNodes_: Mapped[list['ProgressionTreeNodes']] = relationship('ProgressionTreeNodes', secondary='ProgressionTreeNodeTraits', back_populates='Traits')
    Civilizations_: Mapped[list['Civilizations']] = relationship('Civilizations', secondary='CivilizationTraits', back_populates='Traits')
    Districts_: Mapped[list['Districts']] = relationship('Districts', secondary='ExcludedDistricts', back_populates='Traits')
    Leaders_: Mapped[list['Leaders']] = relationship('Leaders', secondary='LeaderTraits', back_populates='Traits')
    LegacyCivilizations_: Mapped[list['LegacyCivilizations']] = relationship('LegacyCivilizations', secondary='LegacyCivilizationTraits', back_populates='Traits')
    Adjacency_YieldChanges: Mapped[list['AdjacencyYieldChanges']] = relationship('AdjacencyYieldChanges', secondary='ExcludedAdjacencies', back_populates='Traits_')
    AiDefinitions: Mapped[list['AiDefinitions']] = relationship('AiDefinitions', back_populates='Traits_')
    Legacies: Mapped[list['Legacies']] = relationship('Legacies', back_populates='Traits_')
    ProgressionTreeNodeUnlocks: Mapped[list['ProgressionTreeNodeUnlocks']] = relationship('ProgressionTreeNodeUnlocks', foreign_keys='[ProgressionTreeNodeUnlocks.NotTraitType]', back_populates='Traits_')
    ProgressionTreeNodeUnlocks_: Mapped[list['ProgressionTreeNodeUnlocks']] = relationship('ProgressionTreeNodeUnlocks', foreign_keys='[ProgressionTreeNodeUnlocks.RequiredTraitType]', back_populates='Traits1')
    Traditions: Mapped[list['Traditions']] = relationship('Traditions', back_populates='Traits_')
    Buildings: Mapped[list['Buildings']] = relationship('Buildings', back_populates='Traits_')
    Improvements: Mapped[list['Improvements']] = relationship('Improvements', back_populates='Traits_')
    Routes: Mapped[list['Routes']] = relationship('Routes', back_populates='Traits_')
    UniqueQuarters: Mapped[list['UniqueQuarters']] = relationship('UniqueQuarters', back_populates='Traits_')
    Units: Mapped[list['Units']] = relationship('Units', back_populates='Traits_')
    GreatPersonClasses: Mapped[list['GreatPersonClasses']] = relationship('GreatPersonClasses', secondary='ExcludedGreatPersonClasses', back_populates='Traits_')


class TypeProperties(Base):
    __tablename__ = 'TypeProperties'

    Name: Mapped[str] = mapped_column(Text, primary_key=True)
    Type: Mapped[str] = mapped_column(ForeignKey('Types.Type', ondelete='CASCADE', onupdate='CASCADE'), primary_key=True)
    PropertyType: Mapped[str] = mapped_column(Text, nullable=False, server_default=text('"PROPERTYTYPE_IDENTITY"'))
    Value: Mapped[str] = mapped_column(Text, nullable=False)

    Types_: Mapped['Types'] = relationship('Types', back_populates='TypeProperties')


class TypeQuotes(Base):
    __tablename__ = 'TypeQuotes'

    Type: Mapped[str] = mapped_column(ForeignKey('Types.Type', ondelete='CASCADE', onupdate='CASCADE'), primary_key=True)
    Quote: Mapped[str] = mapped_column(Text, nullable=False)
    QuoteAudio: Mapped[Optional[str]] = mapped_column(Text)
    QuoteAuthor: Mapped[Optional[str]] = mapped_column(Text)


class TypeTags(Base):
    __tablename__ = 'TypeTags'

    Tag: Mapped[str] = mapped_column(ForeignKey('Tags.Tag', ondelete='CASCADE', onupdate='CASCADE'), primary_key=True)
    Type: Mapped[str] = mapped_column(ForeignKey('Types.Type', ondelete='CASCADE', onupdate='CASCADE'), primary_key=True)
    ShowActivationPlots: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=text('0'))

    Tags_: Mapped['Tags'] = relationship('Tags', back_populates='TypeTags')
    Types_: Mapped['Types'] = relationship('Types', back_populates='TypeTags')


t_Types_ValidAges = Table(
    'Types_ValidAges', Base.metadata,
    Column('GameplayType', ForeignKey('Types.Type', ondelete='CASCADE', onupdate='CASCADE'), primary_key=True),
    Column('ValidAgeType', ForeignKey('Ages.AgeType', ondelete='CASCADE', onupdate='CASCADE'), primary_key=True)
)


class UnitPromotionClasses(Base):
    __tablename__ = 'UnitPromotionClasses'

    PromotionClassType: Mapped[str] = mapped_column(ForeignKey('Types.Type', ondelete='CASCADE', onupdate='CASCADE'), primary_key=True)
    Name: Mapped[str] = mapped_column(Text, nullable=False)

    UnitPromotionDisciplines: Mapped[list['UnitPromotionDisciplines']] = relationship('UnitPromotionDisciplines', secondary='UnitPromotionClassSets', back_populates='UnitPromotionClasses_')
    Units: Mapped[list['Units']] = relationship('Units', back_populates='UnitPromotionClasses_')


class UnitPromotionDisciplines(Base):
    __tablename__ = 'UnitPromotionDisciplines'

    UnitPromotionDisciplineType: Mapped[str] = mapped_column(ForeignKey('Types.Type', ondelete='CASCADE', onupdate='CASCADE'), primary_key=True)
    Name: Mapped[str] = mapped_column(Text, nullable=False)
    BackgroundImage: Mapped[Optional[str]] = mapped_column(Text)

    UnitPromotionClasses_: Mapped[list['UnitPromotionClasses']] = relationship('UnitPromotionClasses', secondary='UnitPromotionClassSets', back_populates='UnitPromotionDisciplines')
    UnitPromotionDisciplineDetails: Mapped[list['UnitPromotionDisciplineDetails']] = relationship('UnitPromotionDisciplineDetails', back_populates='UnitPromotionDisciplines_')


class UnitPromotions(Base):
    __tablename__ = 'UnitPromotions'

    UnitPromotionType: Mapped[str] = mapped_column(ForeignKey('Types.Type', ondelete='CASCADE', onupdate='CASCADE'), primary_key=True)
    Commendation: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=text('0'))
    Description: Mapped[str] = mapped_column(Text, nullable=False)
    Name: Mapped[str] = mapped_column(Text, nullable=False)

    Modifiers_: Mapped[list['Modifiers']] = relationship('Modifiers', secondary='UnitPromotionModifiers', back_populates='UnitPromotions')
    UnitPromotionDisciplineDetails: Mapped[list['UnitPromotionDisciplineDetails']] = relationship('UnitPromotionDisciplineDetails', foreign_keys='[UnitPromotionDisciplineDetails.PrereqUnitPromotion]', back_populates='UnitPromotions_')
    UnitPromotionDisciplineDetails_: Mapped[list['UnitPromotionDisciplineDetails']] = relationship('UnitPromotionDisciplineDetails', foreign_keys='[UnitPromotionDisciplineDetails.UnitPromotionType]', back_populates='UnitPromotions1')


class Unlocks(Base):
    __tablename__ = 'Unlocks'

    UnlockType: Mapped[str] = mapped_column(ForeignKey('Types.Type', ondelete='CASCADE', onupdate='CASCADE'), primary_key=True)

    UnlockRequirements: Mapped[list['UnlockRequirements']] = relationship('UnlockRequirements', back_populates='Unlocks_')


class VictoryCinematics(Base):
    __tablename__ = 'VictoryCinematics'

    VictoryType: Mapped[str] = mapped_column(ForeignKey('Victories.VictoryType', ondelete='CASCADE', onupdate='CASCADE'), primary_key=True)
    Name: Mapped[str] = mapped_column(Text, nullable=False)
    VictoryCinematicType: Mapped[str] = mapped_column(Text, nullable=False)


class AgeCrisisStages(Base):
    __tablename__ = 'AgeCrisisStages'

    AgeCrisisEventType: Mapped[str] = mapped_column(ForeignKey('AgeCrisisEvents.AgeCrisisEventType', ondelete='CASCADE', onupdate='CASCADE'), primary_key=True)
    Stage: Mapped[int] = mapped_column(Integer, primary_key=True)
    AgeProgressEndPercent: Mapped[int] = mapped_column(Integer, nullable=False, server_default=text('0'))
    AgeProgressTriggerPercent: Mapped[int] = mapped_column(Integer, nullable=False, server_default=text('0'))
    FinalStage: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=text('0'))
    MinDuration: Mapped[int] = mapped_column(Integer, nullable=False, server_default=text('0'))

    AgeCrisisEvents_: Mapped['AgeCrisisEvents'] = relationship('AgeCrisisEvents', back_populates='AgeCrisisStages')


class AgeProgressionMilestoneRewards(Base):
    __tablename__ = 'AgeProgressionMilestoneRewards'

    AgeProgressionMilestoneType: Mapped[str] = mapped_column(ForeignKey('AgeProgressionMilestones.AgeProgressionMilestoneType', ondelete='CASCADE', onupdate='CASCADE'), primary_key=True)
    AgeProgressionRewardType: Mapped[str] = mapped_column(ForeignKey('AgeProgressionRewards.AgeProgressionRewardType', ondelete='CASCADE', onupdate='CASCADE'), primary_key=True)
    IsImmediate: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=text('0'))

    AgeProgressionMilestones_: Mapped['AgeProgressionMilestones'] = relationship('AgeProgressionMilestones', back_populates='AgeProgressionMilestoneRewards')
    AgeProgressionRewards_: Mapped['AgeProgressionRewards'] = relationship('AgeProgressionRewards', back_populates='AgeProgressionMilestoneRewards')


class AiDefinitions(Base):
    __tablename__ = 'AiDefinitions'

    AiComponent: Mapped[str] = mapped_column(ForeignKey('AiComponents.Component', ondelete='CASCADE', onupdate='CASCADE'), primary_key=True)
    LeaderTrait: Mapped[str] = mapped_column(ForeignKey('Traits.TraitType', ondelete='SET DEFAULT', onupdate='SET DEFAULT'), primary_key=True)
    ComponentPriority: Mapped[Optional[str]] = mapped_column(ForeignKey('AiPriorities.Priority', ondelete='CASCADE', onupdate='CASCADE'))

    AiComponents_: Mapped['AiComponents'] = relationship('AiComponents', back_populates='AiDefinitions')
    AiPriorities_: Mapped[Optional['AiPriorities']] = relationship('AiPriorities', back_populates='AiDefinitions')
    Traits_: Mapped['Traits'] = relationship('Traits', back_populates='AiDefinitions')


class BeliefModifiers(Base):
    __tablename__ = 'BeliefModifiers'

    BeliefType: Mapped[str] = mapped_column(ForeignKey('Beliefs.BeliefType', ondelete='CASCADE', onupdate='CASCADE'), primary_key=True)
    ModifierID: Mapped[str] = mapped_column(Text, primary_key=True)

    Beliefs_: Mapped['Beliefs'] = relationship('Beliefs', back_populates='BeliefModifiers')


t_Belief_Priorities = Table(
    'Belief_Priorities', Base.metadata,
    Column('BeliefType', ForeignKey('Beliefs.BeliefType', ondelete='CASCADE', onupdate='CASCADE'), primary_key=True),
    Column('ListType', ForeignKey('AiListTypes.ListType', ondelete='CASCADE', onupdate='CASCADE'), primary_key=True)
)


class CityNames(Base):
    __tablename__ = 'CityNames'

    CityName: Mapped[str] = mapped_column(Text, nullable=False)
    SortIndex: Mapped[int] = mapped_column(Integer, nullable=False, server_default=text('0'))
    ID: Mapped[Optional[int]] = mapped_column(Integer, primary_key=True)
    CivilizationType: Mapped[Optional[str]] = mapped_column(ForeignKey('Civilizations.CivilizationType', ondelete='CASCADE', onupdate='CASCADE'))
    ContinentType: Mapped[Optional[str]] = mapped_column(ForeignKey('Continents.ContinentType', ondelete='CASCADE', onupdate='CASCADE'))
    LeaderType: Mapped[Optional[str]] = mapped_column(ForeignKey('Leaders.LeaderType', ondelete='CASCADE', onupdate='CASCADE'))

    Civilizations_: Mapped[Optional['Civilizations']] = relationship('Civilizations', back_populates='CityNames')
    Continents_: Mapped[Optional['Continents']] = relationship('Continents', back_populates='CityNames')
    Leaders_: Mapped[Optional['Leaders']] = relationship('Leaders', back_populates='CityNames')


class CivilizationCitizenNames(Base):
    __tablename__ = 'CivilizationCitizenNames'

    CitizenName: Mapped[str] = mapped_column(Text, primary_key=True)
    CivilizationType: Mapped[str] = mapped_column(ForeignKey('Civilizations.CivilizationType', ondelete='CASCADE', onupdate='CASCADE'), primary_key=True)
    Female: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=text('0'))
    Modern: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=text('0'))

    Civilizations_: Mapped['Civilizations'] = relationship('Civilizations', back_populates='CivilizationCitizenNames')


class CivilizationFavoredWonders(Base):
    __tablename__ = 'CivilizationFavoredWonders'

    CivilizationType: Mapped[str] = mapped_column(ForeignKey('Civilizations.CivilizationType', ondelete='CASCADE', onupdate='CASCADE'), primary_key=True)
    FavoredWonderName: Mapped[Optional[str]] = mapped_column(Text)
    FavoredWonderType: Mapped[Optional[str]] = mapped_column(Text)


class CivilizationInfo(Base):
    __tablename__ = 'CivilizationInfo'

    CivilizationType: Mapped[str] = mapped_column(ForeignKey('Civilizations.CivilizationType', ondelete='CASCADE', onupdate='CASCADE'), primary_key=True)
    Header: Mapped[str] = mapped_column(Text, primary_key=True)
    Caption: Mapped[str] = mapped_column(Text, nullable=False)
    SortIndex: Mapped[int] = mapped_column(Integer, nullable=False, server_default=text('100'))

    Civilizations_: Mapped['Civilizations'] = relationship('Civilizations', back_populates='CivilizationInfo')


t_CivilizationTraits = Table(
    'CivilizationTraits', Base.metadata,
    Column('CivilizationType', ForeignKey('Civilizations.CivilizationType', ondelete='CASCADE', onupdate='CASCADE'), primary_key=True),
    Column('TraitType', ForeignKey('Traits.TraitType', ondelete='CASCADE', onupdate='CASCADE'), primary_key=True)
)


class Constructibles(Base):
    __tablename__ = 'Constructibles'

    ConstructibleType: Mapped[str] = mapped_column(Text, primary_key=True)
    AdjacentLake: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=text('0'))
    AdjacentRiver: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=text('0'))
    Archaeology: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=text('0'))
    CanBeHidden: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=text('0'))
    ConstructibleClass: Mapped[str] = mapped_column(Text, nullable=False)
    Cost: Mapped[int] = mapped_column(Integer, nullable=False)
    CostProgressionModel: Mapped[str] = mapped_column(Text, nullable=False, server_default=text('"NO_COST_PROGRESSION"'))
    CostProgressionParam1: Mapped[int] = mapped_column(Integer, nullable=False, server_default=text('0'))
    Defense: Mapped[int] = mapped_column(Integer, nullable=False, server_default=text('0'))
    Discovery: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=text('0'))
    DistrictDefense: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=text('0'))
    ExistingDistrictOnly: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=text('0'))
    ImmuneDamage: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=text('0'))
    InRailNetwork: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=text('0'))
    IslandSettlement: Mapped[int] = mapped_column(Integer, nullable=False, server_default=text('0'))
    MilitaryDomain: Mapped[str] = mapped_column(Text, nullable=False, server_default=text('"NO_DOMAIN"'))
    Name: Mapped[str] = mapped_column(Text, nullable=False)
    NoFeature: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=text('0'))
    NoRiver: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=text('0'))
    Population: Mapped[int] = mapped_column(Integer, nullable=False)
    ProductionBoostOverRoute: Mapped[int] = mapped_column(Integer, nullable=False, server_default=text('0'))
    Repairable: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=text('1'))
    RequiresAppealPlacement: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=text('0'))
    RequiresDistantLands: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=text('0'))
    RequiresHomeland: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=text('0'))
    RequiresUnlock: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=text('0'))
    VictoryItem: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=text('0'))
    AdjacentDistrict: Mapped[Optional[str]] = mapped_column(ForeignKey('Districts.DistrictType', ondelete='CASCADE', onupdate='CASCADE'))
    AdjacentTerrain: Mapped[Optional[str]] = mapped_column(ForeignKey('Terrains.TerrainType', ondelete='SET DEFAULT', onupdate='SET DEFAULT'))
    Age: Mapped[Optional[str]] = mapped_column(ForeignKey('Ages.AgeType', ondelete='CASCADE', onupdate='CASCADE'))
    Description: Mapped[Optional[str]] = mapped_column(Text)
    RiverPlacement: Mapped[Optional[str]] = mapped_column(Text)
    Tooltip: Mapped[Optional[str]] = mapped_column(Text)

    AdvisoryClasses_: Mapped[list['AdvisoryClasses']] = relationship('AdvisoryClasses', secondary='Constructible_Advisories', back_populates='Constructibles')
    Biomes_: Mapped[list['Biomes']] = relationship('Biomes', secondary='Constructible_InvalidAdjacentBiomes', back_populates='Constructibles')
    Biomes1: Mapped[list['Biomes']] = relationship('Biomes', secondary='Constructible_ValidBiomes', back_populates='Constructibles_')
    Districts_: Mapped[Optional['Districts']] = relationship('Districts', back_populates='Constructibles')
    Terrains_: Mapped[Optional['Terrains']] = relationship('Terrains', back_populates='Constructibles')
    Ages_: Mapped[Optional['Ages']] = relationship('Ages', back_populates='Constructibles')
    Features: Mapped[list['Features']] = relationship('Features', secondary='Constructible_InvalidFeatures', back_populates='Constructibles_')
    FeatureClasses_: Mapped[list['FeatureClasses']] = relationship('FeatureClasses', secondary='Constructible_RequiredFeatureClasses', back_populates='Constructibles')
    Features_: Mapped[list['Features']] = relationship('Features', secondary='Constructible_RequiredFeatures', back_populates='Constructibles1')
    Districts1: Mapped[list['Districts']] = relationship('Districts', secondary='Constructible_ValidDistricts', back_populates='Constructibles_')
    Features1: Mapped[list['Features']] = relationship('Features', secondary='Constructible_ValidFeatures', back_populates='Constructibles2')
    Terrains1: Mapped[list['Terrains']] = relationship('Terrains', secondary='Constructible_ValidTerrains', back_populates='Constructibles_')
    Units: Mapped[list['Units']] = relationship('Units', secondary='Unit_RequiredConstructibles', back_populates='Constructibles_')
    Adjacency_YieldChanges: Mapped[list['AdjacencyYieldChanges']] = relationship('AdjacencyYieldChanges', back_populates='Constructibles_')
    ChargedUnitAbilities: Mapped[list['ChargedUnitAbilities']] = relationship('ChargedUnitAbilities', back_populates='Constructibles_')
    Constructible_AttributePoints: Mapped[list['ConstructibleAttributePoints']] = relationship('ConstructibleAttributePoints', back_populates='Constructibles_')
    Constructible_CitizenYieldChanges: Mapped[list['ConstructibleCitizenYieldChanges']] = relationship('ConstructibleCitizenYieldChanges', back_populates='Constructibles_')
    Constructible_GreatWorks: Mapped[list['ConstructibleGreatWorks']] = relationship('ConstructibleGreatWorks', back_populates='Constructibles_')
    Constructible_Maintenances: Mapped[list['ConstructibleMaintenances']] = relationship('ConstructibleMaintenances', back_populates='Constructibles_')
    Constructible_PillageRandomEvents: Mapped[list['ConstructiblePillageRandomEvents']] = relationship('ConstructiblePillageRandomEvents', back_populates='Constructibles_')
    Constructible_Plunders: Mapped[list['ConstructiblePlunders']] = relationship('ConstructiblePlunders', back_populates='Constructibles_')
    Constructible_ValidResources: Mapped[list['ConstructibleValidResources']] = relationship('ConstructibleValidResources', back_populates='Constructibles_')
    Constructible_YieldChanges: Mapped[list['ConstructibleYieldChanges']] = relationship('ConstructibleYieldChanges', back_populates='Constructibles_')
    GameSystemPrereqs: Mapped[list['GameSystemPrereqs']] = relationship('GameSystemPrereqs', back_populates='Constructibles_')
    IndependentTribeTypes: Mapped[list['IndependentTribeTypes']] = relationship('IndependentTribeTypes', back_populates='Constructibles_')
    Projects: Mapped[list['Projects']] = relationship('Projects', back_populates='Constructibles_')
    Routes: Mapped[list['Routes']] = relationship('Routes', back_populates='Constructibles_')
    UniqueQuarters: Mapped[list['UniqueQuarters']] = relationship('UniqueQuarters', foreign_keys='[UniqueQuarters.BuildingType1]', back_populates='Constructibles_')
    UniqueQuarters_: Mapped[list['UniqueQuarters']] = relationship('UniqueQuarters', foreign_keys='[UniqueQuarters.BuildingType2]', back_populates='Constructibles1')
    Warehouse_YieldChanges: Mapped[list['WarehouseYieldChanges']] = relationship('WarehouseYieldChanges', back_populates='Constructibles_')
    Wonders: Mapped[list['Wonders']] = relationship('Wonders', foreign_keys='[Wonders.AdjacentConstructible]', back_populates='Constructibles_')
    Wonders_: Mapped[list['Wonders']] = relationship('Wonders', foreign_keys='[Wonders.RequiredConstructibleInSettlement]', back_populates='Constructibles1')
    Boosts: Mapped[list['Boosts']] = relationship('Boosts', back_populates='Constructibles_')
    Constructible_Adjacencies: Mapped[list['ConstructibleAdjacencies']] = relationship('ConstructibleAdjacencies', back_populates='Constructibles_')
    Constructible_WarehouseYields: Mapped[list['ConstructibleWarehouseYields']] = relationship('ConstructibleWarehouseYields', back_populates='Constructibles_')
    GreatPersonClasses: Mapped[list['GreatPersonClasses']] = relationship('GreatPersonClasses', back_populates='Constructibles_')
    Unit_BuildConstructibles: Mapped[list['UnitBuildConstructibles']] = relationship('UnitBuildConstructibles', back_populates='Constructibles_')
    Constructible_GreatPersonPoints: Mapped[list['ConstructibleGreatPersonPoints']] = relationship('ConstructibleGreatPersonPoints', back_populates='Constructibles_')
    GreatPersonIndividuals: Mapped[list['GreatPersonIndividuals']] = relationship('GreatPersonIndividuals', foreign_keys='[GreatPersonIndividuals.ActionRequiresCompletedConstructibleType]', back_populates='Constructibles_')
    GreatPersonIndividuals_: Mapped[list['GreatPersonIndividuals']] = relationship('GreatPersonIndividuals', foreign_keys='[GreatPersonIndividuals.ActionRequiresConstructionTypePermission]', back_populates='Constructibles1')
    GreatPersonIndividuals1: Mapped[list['GreatPersonIndividuals']] = relationship('GreatPersonIndividuals', foreign_keys='[GreatPersonIndividuals.ActionRequiresNoConstructibleTypeInCity]', back_populates='Constructibles2')


class DiplomacyBonusEnvoyData(Base):
    __tablename__ = 'DiplomacyBonusEnvoyData'

    DiplomacyActionType: Mapped[str] = mapped_column(ForeignKey('DiplomacyActions.DiplomacyActionType', ondelete='CASCADE', onupdate='CASCADE'), primary_key=True)
    InitialFriendly: Mapped[int] = mapped_column(Integer, nullable=False, server_default=text('0'))
    InitialHelpful: Mapped[int] = mapped_column(Integer, nullable=False, server_default=text('0'))
    InitialHostile: Mapped[int] = mapped_column(Integer, nullable=False, server_default=text('0'))
    InitialUnfriendly: Mapped[int] = mapped_column(Integer, nullable=False, server_default=text('0'))
    TargetFriendly: Mapped[int] = mapped_column(Integer, nullable=False, server_default=text('0'))
    TargetHelpful: Mapped[int] = mapped_column(Integer, nullable=False, server_default=text('0'))
    TargetHostile: Mapped[int] = mapped_column(Integer, nullable=False, server_default=text('0'))
    TargetUnfriendly: Mapped[int] = mapped_column(Integer, nullable=False, server_default=text('0'))


class DiplomaticActionResponseModifiers(Base):
    __tablename__ = 'DiplomaticActionResponseModifiers'

    DiplomacyActionType: Mapped[str] = mapped_column(ForeignKey('DiplomacyActions.DiplomacyActionType', ondelete='CASCADE', onupdate='CASCADE'), primary_key=True)
    DiplomaticResponseType: Mapped[str] = mapped_column(ForeignKey('Types.Type', ondelete='CASCADE', onupdate='CASCADE'), primary_key=True)
    ModifierId: Mapped[str] = mapped_column(Text, primary_key=True)
    ModifierTarget: Mapped[str] = mapped_column(Text, nullable=False)
    ModifierType: Mapped[str] = mapped_column(Text, nullable=False)

    DiplomacyActions_: Mapped['DiplomacyActions'] = relationship('DiplomacyActions', back_populates='DiplomaticActionResponseModifiers')
    Types_: Mapped['Types'] = relationship('Types', back_populates='DiplomaticActionResponseModifiers')


class DiplomaticActionResponses(Base):
    __tablename__ = 'DiplomaticActionResponses'

    DiplomacyActionType: Mapped[str] = mapped_column(ForeignKey('DiplomacyActions.DiplomacyActionType', ondelete='CASCADE', onupdate='CASCADE'), primary_key=True)
    DiplomaticResponseType: Mapped[str] = mapped_column(ForeignKey('Types.Type', ondelete='CASCADE', onupdate='CASCADE'), primary_key=True)
    CostDescription: Mapped[str] = mapped_column(Text, nullable=False, server_default=text('"LOC_DIPLOMACY_ACTION_COST_YIELD_DIPLOMACY"'))
    Description: Mapped[str] = mapped_column(Text, nullable=False, server_default=text('"LOC_DIPLOMACY_ACTION_MISSING_DATA"'))
    InfCost: Mapped[int] = mapped_column(Integer, nullable=False, server_default=text('0'))
    Name: Mapped[str] = mapped_column(Text, nullable=False, server_default=text('"LOC_DIPLOMACY_ACTION_MISSING_NAME"'))

    DiplomacyActions_: Mapped['DiplomacyActions'] = relationship('DiplomacyActions', back_populates='DiplomaticActionResponses')
    Types_: Mapped['Types'] = relationship('Types', back_populates='DiplomaticActionResponses')


class DiplomaticActionStages(Base):
    __tablename__ = 'DiplomaticActionStages'

    StageType: Mapped[str] = mapped_column(ForeignKey('Types.Type', ondelete='CASCADE', onupdate='CASCADE'), primary_key=True)
    CheckForCounterSpy: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=text('0'))
    CheckForFailure: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=text('0'))
    CheckForReveal: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=text('0'))
    CheckForTurnedBasedInfluenceCost: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=text('0'))
    DiplomacyActionType: Mapped[str] = mapped_column(ForeignKey('DiplomacyActions.DiplomacyActionType', ondelete='CASCADE', onupdate='CASCADE'), nullable=False)
    ProgressRequirement: Mapped[int] = mapped_column(Integer, nullable=False, server_default=text('0'))
    Description: Mapped[Optional[str]] = mapped_column(Text)
    Name: Mapped[Optional[str]] = mapped_column(Text)
    OtherPlayerNotificationMessage: Mapped[Optional[str]] = mapped_column(Text)
    OtherPlayerNotificationSummary: Mapped[Optional[str]] = mapped_column(Text)
    OwnerNotificationMessage: Mapped[Optional[str]] = mapped_column(Text)
    OwnerNotificationSummary: Mapped[Optional[str]] = mapped_column(Text)
    StageIconPath: Mapped[Optional[str]] = mapped_column(Text)
    StageToolTip: Mapped[Optional[str]] = mapped_column(Text)

    DiplomacyActions_: Mapped['DiplomacyActions'] = relationship('DiplomacyActions', back_populates='DiplomaticActionStages')
    EnterStageModifiers: Mapped[list['EnterStageModifiers']] = relationship('EnterStageModifiers', back_populates='DiplomaticActionStages_')
    EnvoysInStageModifiers: Mapped[list['EnvoysInStageModifiers']] = relationship('EnvoysInStageModifiers', back_populates='DiplomaticActionStages_')


t_DiplomaticActionValidTokens = Table(
    'DiplomaticActionValidTokens', Base.metadata,
    Column('DiplomacyActionType', ForeignKey('DiplomacyActions.DiplomacyActionType', ondelete='CASCADE', onupdate='CASCADE'), primary_key=True),
    Column('TokenType', ForeignKey('Types.Type', ondelete='CASCADE', onupdate='CASCADE'), primary_key=True)
)


class DiplomaticProjectsUIData(Base):           # NOTE Kept inheritance
    __tablename__ = 'DiplomaticProjects_UI_Data'

    DiplomacyActionType: Mapped[str] = mapped_column(ForeignKey('DiplomacyActions.DiplomacyActionType', ondelete='CASCADE', onupdate='CASCADE'), primary_key=True)
    CostInGold: Mapped[int] = mapped_column(Integer, nullable=False, server_default=text('0'))
    Description: Mapped[str] = mapped_column(Text, nullable=False)
    DiplomacyActionGroup: Mapped[str] = mapped_column(ForeignKey('DiplomacyActionGroups.DiplomacyActionGroupType', ondelete='CASCADE', onupdate='CASCADE'), nullable=False)
    DiplomacyActionGroupSubtype: Mapped[str] = mapped_column(ForeignKey('Types.Type', ondelete='CASCADE', onupdate='CASCADE'), nullable=False, server_default=text('"DIPLOMACY_ACTION_GROUP_SUBTYPE_NORMAL"'))
    MaxNumEnvoys: Mapped[int] = mapped_column(Integer, nullable=False, server_default=text('-1'))
    MaxNumOpposeEnvoys: Mapped[int] = mapped_column(Integer, nullable=False, server_default=text('-1'))
    MaxNumSupportEnvoys: Mapped[int] = mapped_column(Integer, nullable=False, server_default=text('-1'))
    MaxNumVirtEnvoys: Mapped[int] = mapped_column(Integer, nullable=False, server_default=text('-1'))
    MinNumVirtEnvoys: Mapped[int] = mapped_column(Integer, nullable=False, server_default=text('-1'))
    PlayerOperationType: Mapped[str] = mapped_column(Text, nullable=False)
    SupportWindowSize: Mapped[int] = mapped_column(Integer, nullable=False, server_default=text('-1'))
    UIOnly_BaseAmount: Mapped[int] = mapped_column(Integer, nullable=False, server_default=text('0'))
    UIOnly_GivesYieldType: Mapped[str] = mapped_column(Text, nullable=False, server_default=text('"NO_YIELD"'))
    UIOnly_SupportAmount: Mapped[int] = mapped_column(Integer, nullable=False, server_default=text('0'))
    UIShowActiveProject: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=text('1'))
    UIStartProject: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=text('1'))
    ActiveDescription: Mapped[Optional[str]] = mapped_column(Text)
    CostDescription: Mapped[Optional[str]] = mapped_column(Text)
    DescriptionDetailsInitialPlayer: Mapped[Optional[str]] = mapped_column(Text)
    DescriptionDetailsTargetPlayer: Mapped[Optional[str]] = mapped_column(Text)
    Target1Type: Mapped[Optional[str]] = mapped_column(Text)
    Target2Type: Mapped[Optional[str]] = mapped_column(Text)

    DiplomacyActionGroups_: Mapped['DiplomacyActionGroups'] = relationship('DiplomacyActionGroups', back_populates='DiplomaticProjects_UI_Data')
    Types_: Mapped['Types'] = relationship('Types', back_populates='DiplomaticProjects_UI_Data')


t_EndGameMovies = Table(
    'EndGameMovies', Base.metadata,
    Column('AgeType', ForeignKey('Ages.AgeType', ondelete='CASCADE', onupdate='CASCADE')),
    Column('CivilizationType', ForeignKey('Civilizations.CivilizationType', ondelete='CASCADE', onupdate='CASCADE')),
    Column('CompletedLegacyPath', ForeignKey('LegacyPaths.LegacyPathType', ondelete='CASCADE', onupdate='CASCADE')),
    Column('DefeatType', ForeignKey('Defeats.DefeatType', ondelete='CASCADE', onupdate='CASCADE')),
    Column('IsFinalAge', Boolean),
    Column('LastCompletedLegacyPath', ForeignKey('LegacyPaths.LegacyPathType', ondelete='CASCADE', onupdate='CASCADE')),
    Column('LeaderType', ForeignKey('Leaders.LeaderType', ondelete='CASCADE', onupdate='CASCADE')),
    Column('MovieType', Text, nullable=False),
    Column('Priority', Integer, nullable=False, server_default=text('0')),
    Column('UnlockType', Text),
    Column('VictoryType', ForeignKey('Victories.VictoryType', ondelete='CASCADE', onupdate='CASCADE'))
)


class EnvoysInActionModifiers(Base):
    __tablename__ = 'EnvoysInActionModifiers'

    DiplomacyActionType: Mapped[str] = mapped_column(ForeignKey('DiplomacyActions.DiplomacyActionType', ondelete='CASCADE', onupdate='CASCADE'), primary_key=True)
    ModifierId: Mapped[str] = mapped_column(ForeignKey('Modifiers.ModifierId', ondelete='CASCADE', onupdate='CASCADE'), primary_key=True)
    NumEnvoys: Mapped[int] = mapped_column(Integer, nullable=False, server_default=text('0'))

    DiplomacyActions_: Mapped['DiplomacyActions'] = relationship('DiplomacyActions', back_populates='EnvoysInActionModifiers')
    Modifiers_: Mapped['Modifiers'] = relationship('Modifiers', back_populates='EnvoysInActionModifiers')


t_ExcludedDistricts = Table(
    'ExcludedDistricts', Base.metadata,
    Column('DistrictType', ForeignKey('Districts.DistrictType', ondelete='CASCADE', onupdate='CASCADE'), primary_key=True),
    Column('TraitType', ForeignKey('Traits.TraitType', ondelete='CASCADE', onupdate='CASCADE'), primary_key=True)
)


class FavoredReligions(Base):
    __tablename__ = 'FavoredReligions'

    ReligionType: Mapped[str] = mapped_column(ForeignKey('Religions.ReligionType', ondelete='CASCADE', onupdate='CASCADE'), primary_key=True)
    CivilizationType: Mapped[Optional[str]] = mapped_column(ForeignKey('Civilizations.CivilizationType', ondelete='CASCADE', onupdate='CASCADE'), primary_key=True, nullable=True)
    LeaderType: Mapped[Optional[str]] = mapped_column(ForeignKey('Leaders.LeaderType', ondelete='CASCADE', onupdate='CASCADE'), primary_key=True, nullable=True)

    Civilizations_: Mapped[Optional['Civilizations']] = relationship('Civilizations', back_populates='FavoredReligions')
    Leaders_: Mapped[Optional['Leaders']] = relationship('Leaders', back_populates='FavoredReligions')
    Religions_: Mapped['Religions'] = relationship('Religions', back_populates='FavoredReligions')


class Features(Base):
    __tablename__ = 'Features'

    FeatureType: Mapped[str] = mapped_column(ForeignKey('Types.Type', ondelete='CASCADE', onupdate='CASCADE'), primary_key=True)
    AddsFreshWater: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=text('0'))
    AllowSettlement: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=text('1'))
    AntiquityPriority: Mapped[int] = mapped_column(Integer, nullable=False, server_default=text('0'))
    Appeal: Mapped[int] = mapped_column(Integer, nullable=False, server_default=text('0'))
    DefenseModifier: Mapped[int] = mapped_column(Integer, nullable=False, server_default=text('0'))
    Impassable: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=text('0'))
    MaximumElevation: Mapped[int] = mapped_column(Integer, nullable=False, server_default=text('0'))
    MaxLatitude: Mapped[int] = mapped_column(Integer, nullable=False, server_default=text('0'))
    MinimumElevation: Mapped[int] = mapped_column(Integer, nullable=False, server_default=text('0'))
    MinLatitude: Mapped[int] = mapped_column(Integer, nullable=False, server_default=text('0'))
    MovementChange: Mapped[int] = mapped_column(Integer, nullable=False, server_default=text('0'))
    Name: Mapped[str] = mapped_column(Text, nullable=False)
    NoLake: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=text('0'))
    PlacementClass: Mapped[str] = mapped_column(Text, nullable=False)
    PlacementDensity: Mapped[int] = mapped_column(Integer, nullable=False, server_default=text('0'))
    Removable: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=text('0'))
    SightThroughModifier: Mapped[int] = mapped_column(Integer, nullable=False, server_default=text('0'))
    Description: Mapped[Optional[str]] = mapped_column(Text)
    FeatureClassType: Mapped[Optional[str]] = mapped_column(ForeignKey('FeatureClasses.FeatureClassType', ondelete='CASCADE', onupdate='CASCADE'))
    PreventUnpack: Mapped[Optional[bool]] = mapped_column(Boolean, server_default=text('0'))
    Tooltip: Mapped[Optional[str]] = mapped_column(Text)

    Districts_: Mapped[list['Districts']] = relationship('Districts', secondary='District_RemovedFeatures', back_populates='Features')
    Constructibles_: Mapped[list['Constructibles']] = relationship('Constructibles', secondary='Constructible_InvalidFeatures', back_populates='Features')
    Constructibles1: Mapped[list['Constructibles']] = relationship('Constructibles', secondary='Constructible_RequiredFeatures', back_populates='Features_')
    Constructibles2: Mapped[list['Constructibles']] = relationship('Constructibles', secondary='Constructible_ValidFeatures', back_populates='Features1')
    FeatureClasses_: Mapped[Optional['FeatureClasses']] = relationship('FeatureClasses', back_populates='Features')
    Features: Mapped[list['Features']] = relationship('Features', secondary='Feature_AdjacentFeatures', primaryjoin=lambda: Features.FeatureType == t_Feature_AdjacentFeatures.c.FeatureType, secondaryjoin=lambda: Features.FeatureType == t_Feature_AdjacentFeatures.c.FeatureTypeAdjacent, back_populates='Features_')
    Features_: Mapped[list['Features']] = relationship('Features', secondary='Feature_AdjacentFeatures', primaryjoin=lambda: Features.FeatureType == t_Feature_AdjacentFeatures.c.FeatureTypeAdjacent, secondaryjoin=lambda: Features.FeatureType == t_Feature_AdjacentFeatures.c.FeatureType, back_populates='Features')
    Terrains_: Mapped[list['Terrains']] = relationship('Terrains', secondary='Feature_AdjacentTerrains', back_populates='Features')
    Terrains1: Mapped[list['Terrains']] = relationship('Terrains', secondary='Feature_NotAdjacentTerrains', back_populates='Features_')
    Features1: Mapped[list['Features']] = relationship('Features', secondary='Feature_NotNearFeatures', primaryjoin=lambda: Features.FeatureType == t_Feature_NotNearFeatures.c.FeatureType, secondaryjoin=lambda: Features.FeatureType == t_Feature_NotNearFeatures.c.FeatureTypeAvoid, back_populates='Features2')
    Features2: Mapped[list['Features']] = relationship('Features', secondary='Feature_NotNearFeatures', primaryjoin=lambda: Features.FeatureType == t_Feature_NotNearFeatures.c.FeatureTypeAvoid, secondaryjoin=lambda: Features.FeatureType == t_Feature_NotNearFeatures.c.FeatureType, back_populates='Features1')
    Terrains2: Mapped[list['Terrains']] = relationship('Terrains', secondary='Feature_ValidTerrains', back_populates='Features1')
    Adjacency_YieldChanges: Mapped[list['AdjacencyYieldChanges']] = relationship('AdjacencyYieldChanges', back_populates='Features_')
    Feature_CityYields: Mapped[list['FeatureCityYields']] = relationship('FeatureCityYields', back_populates='Features_')
    Feature_Removes: Mapped[list['FeatureRemoves']] = relationship('FeatureRemoves', back_populates='Features_')
    Feature_ValidBiomes: Mapped[list['FeatureValidBiomes']] = relationship('FeatureValidBiomes', back_populates='Features_')
    RandomEvents: Mapped[list['RandomEvents']] = relationship('RandomEvents', back_populates='Features_')
    RegionClaimObstacles: Mapped[list['RegionClaimObstacles']] = relationship('RegionClaimObstacles', back_populates='Features_')
    Resource_ValidBiomes: Mapped[list['ResourceValidBiomes']] = relationship('ResourceValidBiomes', back_populates='Features_')
    TerrainBiomeFeature_YieldChanges: Mapped[list['TerrainBiomeFeatureYieldChanges']] = relationship('TerrainBiomeFeatureYieldChanges', back_populates='Features_')
    UnitMovementClassObstacles: Mapped[list['UnitMovementClassObstacles']] = relationship('UnitMovementClassObstacles', back_populates='Features_')
    Warehouse_YieldChanges: Mapped[list['WarehouseYieldChanges']] = relationship('WarehouseYieldChanges', back_populates='Features_')
    GreatPersonIndividuals: Mapped[list['GreatPersonIndividuals']] = relationship('GreatPersonIndividuals', back_populates='Features_')


class GameCapabilityDependencies(Base):
    __tablename__ = 'GameCapabilityDependencies'

    ID: Mapped[Optional[int]] = mapped_column(Integer, primary_key=True)
    DependsOnCapability: Mapped[Optional[str]] = mapped_column(ForeignKey('GameCapabilities.GameCapability', ondelete='CASCADE', onupdate='CASCADE'))
    GameCapability: Mapped[Optional[int]] = mapped_column(ForeignKey('GameCapabilities.GameCapability', ondelete='CASCADE', onupdate='CASCADE'))

    GameCapabilities_: Mapped[Optional['GameCapabilities']] = relationship('GameCapabilities', foreign_keys=[DependsOnCapability], back_populates='GameCapabilityDependencies')
    GameCapabilities1: Mapped[Optional['GameCapabilities']] = relationship('GameCapabilities', foreign_keys=[GameCapability], back_populates='GameCapabilityDependencies_')


class GameEffectArguments(Base):
    __tablename__ = 'GameEffectArguments'

    Name: Mapped[str] = mapped_column(Text, primary_key=True)
    Required: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=text('0'))
    Type: Mapped[Optional[str]] = mapped_column(ForeignKey('GameEffects.Type', ondelete='CASCADE', onupdate='CASCADE'), primary_key=True, nullable=True)
    ArgumentType: Mapped[Optional[str]] = mapped_column(Text)
    DatabaseKind: Mapped[Optional[str]] = mapped_column(Text)
    DefaultValue: Mapped[Optional[str]] = mapped_column(Text)
    Description: Mapped[Optional[str]] = mapped_column(Text)
    MaxValue: Mapped[Optional[str]] = mapped_column(Text)
    MinValue: Mapped[Optional[str]] = mapped_column(Text)

    GameEffects_: Mapped[Optional['GameEffects']] = relationship('GameEffects', back_populates='GameEffectArguments')


class IdeologyAdoptionModifiers(Base):
    __tablename__ = 'IdeologyAdoptionModifiers'

    AdoptionOrder: Mapped[int] = mapped_column(Integer, primary_key=True)
    IdeologyType: Mapped[str] = mapped_column(ForeignKey('Ideologies.IdeologyType', ondelete='CASCADE', onupdate='CASCADE'), primary_key=True)
    ModifierId: Mapped[str] = mapped_column(Text, nullable=False)

    Ideologies_: Mapped['Ideologies'] = relationship('Ideologies', back_populates='IdeologyAdoptionModifiers')


class IdeologyPriorities(Base):
    __tablename__ = 'IdeologyPriorities'

    AiListType: Mapped[str] = mapped_column(Text, primary_key=True)
    IdeologyType: Mapped[str] = mapped_column(ForeignKey('Ideologies.IdeologyType', ondelete='CASCADE', onupdate='CASCADE'), primary_key=True)

    Ideologies_: Mapped['Ideologies'] = relationship('Ideologies', back_populates='IdeologyPriorities')


class LeaderCivPriorities(Base):
    __tablename__ = 'LeaderCivPriorities'

    Civilization: Mapped[str] = mapped_column(ForeignKey('Civilizations.CivilizationType', ondelete='CASCADE', onupdate='CASCADE'), primary_key=True)
    Leader: Mapped[str] = mapped_column(ForeignKey('Leaders.LeaderType', ondelete='CASCADE', onupdate='CASCADE'), primary_key=True)
    Priority: Mapped[int] = mapped_column(Integer, nullable=False)

    Civilizations_: Mapped['Civilizations'] = relationship('Civilizations', back_populates='LeaderCivPriorities')
    Leaders_: Mapped['Leaders'] = relationship('Leaders', back_populates='LeaderCivPriorities')


class LeaderInfo(Base):
    __tablename__ = 'LeaderInfo'

    Header: Mapped[str] = mapped_column(Text, primary_key=True)
    LeaderType: Mapped[str] = mapped_column(ForeignKey('Leaders.LeaderType', ondelete='CASCADE', onupdate='CASCADE'), primary_key=True)
    Caption: Mapped[str] = mapped_column(Text, nullable=False)
    SortIndex: Mapped[int] = mapped_column(Integer, nullable=False, server_default=text('100'))

    Leaders_: Mapped['Leaders'] = relationship('Leaders', back_populates='LeaderInfo')


t_LeaderTraits = Table(
    'LeaderTraits', Base.metadata,
    Column('LeaderType', ForeignKey('Leaders.LeaderType', ondelete='CASCADE', onupdate='CASCADE'), primary_key=True),
    Column('TraitType', ForeignKey('Traits.TraitType', ondelete='CASCADE', onupdate='CASCADE'), primary_key=True)
)


class Legacies(Base):
    __tablename__ = 'Legacies'

    LegacyType: Mapped[str] = mapped_column(Text, primary_key=True)
    Age: Mapped[str] = mapped_column(ForeignKey('Ages.AgeType', ondelete='CASCADE', onupdate='CASCADE'), nullable=False)
    Description: Mapped[str] = mapped_column(Text, nullable=False)
    FirstPlayerOnly: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=text('0'))
    Name: Mapped[str] = mapped_column(Text, nullable=False)
    TriggerDescription: Mapped[str] = mapped_column(Text, nullable=False)
    ProgressString: Mapped[Optional[str]] = mapped_column(Text)
    TraitType: Mapped[Optional[str]] = mapped_column(ForeignKey('Traits.TraitType', ondelete='CASCADE', onupdate='CASCADE'))

    Ages_: Mapped['Ages'] = relationship('Ages', back_populates='Legacies')
    Traits_: Mapped[Optional['Traits']] = relationship('Traits', back_populates='Legacies')
    Legacy_LegacySets: Mapped[list['LegacyLegacySets']] = relationship('LegacyLegacySets', back_populates='Legacies_')


t_LegacyCivilizationTraits = Table(
    'LegacyCivilizationTraits', Base.metadata,
    Column('CivilizationType', ForeignKey('LegacyCivilizations.CivilizationType', ondelete='CASCADE', onupdate='CASCADE'), primary_key=True),
    Column('TraitType', ForeignKey('Traits.TraitType', ondelete='CASCADE', onupdate='CASCADE'), primary_key=True)
)


class LegacyLeaderCivPriorities(Base):
    __tablename__ = 'LegacyLeaderCivPriorities'

    CivilizationType: Mapped[str] = mapped_column(Text, primary_key=True)
    Leader: Mapped[str] = mapped_column(ForeignKey('Leaders.LeaderType', ondelete='CASCADE', onupdate='CASCADE'), primary_key=True)

    Leaders_: Mapped['Leaders'] = relationship('Leaders', back_populates='LegacyLeaderCivPriorities')


class LoadingInfoCivilizations(Civilizations):          # NOTE kept inheritance
    __tablename__ = 'LoadingInfo_Civilizations'

    CivilizationType: Mapped[str] = mapped_column(ForeignKey('Civilizations.CivilizationType', ondelete='CASCADE', onupdate='CASCADE'), primary_key=True)
    AgeTypeOverride: Mapped[Optional[str]] = mapped_column(Text)
    Audio: Mapped[Optional[str]] = mapped_column(Text)
    BackgroundImageHigh: Mapped[Optional[str]] = mapped_column(Text)
    BackgroundImageLow: Mapped[Optional[str]] = mapped_column(Text)
    CivilizationNameTextOverride: Mapped[Optional[str]] = mapped_column(Text)
    CivilizationText: Mapped[Optional[str]] = mapped_column(Text)
    ForegroundImage: Mapped[Optional[str]] = mapped_column(Text)
    LeaderTypeOverride: Mapped[Optional[str]] = mapped_column(Text)
    MidgroundImage: Mapped[Optional[str]] = mapped_column(Text)
    Subtitle: Mapped[Optional[str]] = mapped_column(Text)
    Tip: Mapped[Optional[str]] = mapped_column(Text)


class LoadingInfoLeaders(Leaders):          # NOTE kept inheritance
    __tablename__ = 'LoadingInfo_Leaders'

    LeaderType: Mapped[str] = mapped_column(ForeignKey('Leaders.LeaderType', ondelete='CASCADE', onupdate='CASCADE'), primary_key=True)
    AgeTypeOverride: Mapped[Optional[str]] = mapped_column(Text)
    Audio: Mapped[Optional[str]] = mapped_column(Text)
    CivilizationTypeOverride: Mapped[Optional[str]] = mapped_column(Text)
    LeaderImage: Mapped[Optional[str]] = mapped_column(Text)
    LeaderNameTextOverride: Mapped[Optional[str]] = mapped_column(Text)
    LeaderText: Mapped[Optional[str]] = mapped_column(Text)


class MetaprogressionModifiers(Base):
    __tablename__ = 'MetaprogressionModifiers'

    ModifierId: Mapped[str] = mapped_column(Text, primary_key=True)
    RequiredCivilizationType: Mapped[Optional[str]] = mapped_column(ForeignKey('Civilizations.CivilizationType', ondelete='CASCADE', onupdate='CASCADE'))
    RequiredLeaderType: Mapped[Optional[str]] = mapped_column(ForeignKey('Leaders.LeaderType', ondelete='CASCADE', onupdate='CASCADE'))

    Civilizations_: Mapped[Optional['Civilizations']] = relationship('Civilizations', back_populates='MetaprogressionModifiers')
    Leaders_: Mapped[Optional['Leaders']] = relationship('Leaders', back_populates='MetaprogressionModifiers')


class NarrativeDisplayCivilizations(Civilizations):                               # NOTE kept inheritance maybe shouldnt?
    __tablename__ = 'NarrativeDisplay_Civilizations'

    CivilizationType: Mapped[str] = mapped_column(ForeignKey('Civilizations.CivilizationType', ondelete='CASCADE', onupdate='CASCADE'), primary_key=True)
    CivilizationImage: Mapped[Optional[str]] = mapped_column(Text)


class NarrativeRewardIcons(Base):
    __tablename__ = 'NarrativeRewardIcons'

    NarrativeStoryType: Mapped[str] = mapped_column(ForeignKey('NarrativeStories.NarrativeStoryType', ondelete='CASCADE', onupdate='CASCADE'), primary_key=True)
    Negative: Mapped[bool] = mapped_column(Boolean, primary_key=True, server_default=text('0'))
    RewardIconType: Mapped[str] = mapped_column(Text, primary_key=True)

    NarrativeStories_: Mapped['NarrativeStories'] = relationship('NarrativeStories', back_populates='NarrativeRewardIcons')


class NarrativeStoryOverrides(Base):
    __tablename__ = 'NarrativeStoryOverrides'

    NarrativeStoryType: Mapped[str] = mapped_column(ForeignKey('NarrativeStories.NarrativeStoryType', ondelete='CASCADE', onupdate='CASCADE'), primary_key=True)
    OverriddenStoryType: Mapped[str] = mapped_column(Text, primary_key=True)

    NarrativeStories_: Mapped['NarrativeStories'] = relationship('NarrativeStories', back_populates='NarrativeStoryOverrides')


class NarrativeStoryLinks(Base):
    __tablename__ = 'NarrativeStory_Links'

    FromNarrativeStoryType: Mapped[str] = mapped_column(ForeignKey('NarrativeStories.NarrativeStoryType', ondelete='CASCADE', onupdate='CASCADE'), primary_key=True)
    ToNarrativeStoryType: Mapped[str] = mapped_column(Text, primary_key=True)
    Description: Mapped[str] = mapped_column(Text, nullable=False)
    Name: Mapped[str] = mapped_column(Text, nullable=False)
    Priority: Mapped[int] = mapped_column(Integer, nullable=False, server_default=text('0'))
    Imperative: Mapped[Optional[str]] = mapped_column(Text)

    NarrativeStories_: Mapped['NarrativeStories'] = relationship('NarrativeStories', back_populates='NarrativeStory_Links')


class NarrativeStoryRewards(Base):
    __tablename__ = 'NarrativeStory_Rewards'

    NarrativeRewardType: Mapped[str] = mapped_column(ForeignKey('NarrativeRewards.NarrativeRewardType', ondelete='CASCADE', onupdate='CASCADE'), primary_key=True)
    NarrativeStoryType: Mapped[str] = mapped_column(ForeignKey('NarrativeStories.NarrativeStoryType', ondelete='CASCADE', onupdate='CASCADE'), primary_key=True)
    Activation: Mapped[str] = mapped_column(ForeignKey('NarrativeStory_Reward_Activations.Type', ondelete='CASCADE', onupdate='CASCADE'), nullable=False)
    BonusEligible: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=text('1'))

    NarrativeStory_Reward_Activations: Mapped['NarrativeStoryRewardActivations'] = relationship('NarrativeStoryRewardActivations', back_populates='NarrativeStory_Rewards')
    NarrativeRewards_: Mapped['NarrativeRewards'] = relationship('NarrativeRewards', back_populates='NarrativeStory_Rewards')
    NarrativeStories_: Mapped['NarrativeStories'] = relationship('NarrativeStories', back_populates='NarrativeStory_Rewards')


class NarrativeStoryTextReplacements(Base):
    __tablename__ = 'NarrativeStory_TextReplacements'

    NarrativeStoryTextType: Mapped[str] = mapped_column(Text, primary_key=True)
    NarrativeStoryType: Mapped[str] = mapped_column(ForeignKey('NarrativeStories.NarrativeStoryType', ondelete='CASCADE', onupdate='CASCADE'), primary_key=True)
    Priority: Mapped[int] = mapped_column(Integer, primary_key=True, server_default=text('0'))
    NarrativeTextReplacementType: Mapped[str] = mapped_column(Text, nullable=False)

    NarrativeStories_: Mapped['NarrativeStories'] = relationship('NarrativeStories', back_populates='NarrativeStory_TextReplacements')


class NarrativeVariations(Base):
    __tablename__ = 'NarrativeVariations'

    NarrativeStoryType: Mapped[str] = mapped_column(ForeignKey('NarrativeStories.NarrativeStoryType', ondelete='CASCADE', onupdate='CASCADE'), primary_key=True)
    VariationStoryType: Mapped[str] = mapped_column(Text, primary_key=True)

    NarrativeStories_: Mapped['NarrativeStories'] = relationship('NarrativeStories', back_populates='NarrativeVariations')


t_ProgressionTreeNodeTraits = Table(
    'ProgressionTreeNodeTraits', Base.metadata,
    Column('ProgressionTreeNodeType', ForeignKey('ProgressionTreeNodes.ProgressionTreeNodeType', ondelete='CASCADE', onupdate='CASCADE'), primary_key=True),
    Column('RequiredTraitType', ForeignKey('Traits.TraitType', ondelete='SET DEFAULT', onupdate='SET DEFAULT'))
)


class ProgressionTreeNodeUnlocks(Base):
    __tablename__ = 'ProgressionTreeNodeUnlocks'

    ProgressionTreeNodeType: Mapped[str] = mapped_column(ForeignKey('ProgressionTreeNodes.ProgressionTreeNodeType', ondelete='CASCADE', onupdate='CASCADE'), primary_key=True)
    TargetType: Mapped[str] = mapped_column(Text, primary_key=True)
    AIIgnoreUnlockValue: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=text('0'))
    TargetKind: Mapped[str] = mapped_column(Text, nullable=False)
    UnlockDepth: Mapped[int] = mapped_column(Integer, nullable=False, server_default=text('1'))
    Hidden: Mapped[Optional[bool]] = mapped_column(Boolean)
    IconString: Mapped[Optional[str]] = mapped_column(Text)
    NotTraitType: Mapped[Optional[str]] = mapped_column(ForeignKey('Traits.TraitType', ondelete='SET DEFAULT', onupdate='SET DEFAULT'))
    RequiredTraitType: Mapped[Optional[str]] = mapped_column(ForeignKey('Traits.TraitType', ondelete='SET DEFAULT', onupdate='SET DEFAULT'))

    Traits_: Mapped[Optional['Traits']] = relationship('Traits', foreign_keys=[NotTraitType], back_populates='ProgressionTreeNodeUnlocks')
    ProgressionTreeNodes_: Mapped['ProgressionTreeNodes'] = relationship('ProgressionTreeNodes', back_populates='ProgressionTreeNodeUnlocks')
    Traits1: Mapped[Optional['Traits']] = relationship('Traits', foreign_keys=[RequiredTraitType], back_populates='ProgressionTreeNodeUnlocks_')


class RandomEventUI(Base):
    __tablename__ = 'RandomEventUI'

    EventClass: Mapped[str] = mapped_column(ForeignKey('EventClasses.EventClass', ondelete='CASCADE', onupdate='CASCADE'), primary_key=True)
    Tooltip: Mapped[str] = mapped_column(Text, nullable=False)


class ResourceClassApplicableLegacyPaths(Base):
    __tablename__ = 'ResourceClassApplicableLegacyPaths'

    LegacyPathType: Mapped[str] = mapped_column(ForeignKey('LegacyPaths.LegacyPathType', ondelete='CASCADE', onupdate='CASCADE'), primary_key=True)
    ResourceClassType: Mapped[str] = mapped_column(ForeignKey('ResourceClasses.ResourceClassType', ondelete='CASCADE', onupdate='CASCADE'), primary_key=True)
    MinimumPerMap: Mapped[int] = mapped_column(Integer, nullable=False, server_default=text('0'))

    LegacyPaths_: Mapped['LegacyPaths'] = relationship('LegacyPaths', back_populates='ResourceClassApplicableLegacyPaths')
    ResourceClasses_: Mapped['ResourceClasses'] = relationship('ResourceClasses', back_populates='ResourceClassApplicableLegacyPaths')


class Resources(Base):
    __tablename__ = 'Resources'

    ResourceType: Mapped[str] = mapped_column(ForeignKey('Types.Type', ondelete='CASCADE', onupdate='CASCADE'), primary_key=True)
    AdjacentToLand: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=text('0'))
    AssignCoastal: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=text('0'))
    AssignInland: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=text('0'))
    BonusResourceSlots: Mapped[int] = mapped_column(Integer, nullable=False, server_default=text('0'))
    Clumped: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=text('0'))
    HemisphereUnique: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=text('0'))
    IsPendingGenerationUpdate: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=text('0'))
    LakeEligible: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=text('1'))
    MinimumPerHemisphere: Mapped[int] = mapped_column(Integer, nullable=False, server_default=text('3'))
    Name: Mapped[str] = mapped_column(Text, nullable=False)
    NoRiver: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=text('0'))
    RequiresRiver: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=text('0'))
    ResourceClassType: Mapped[str] = mapped_column(ForeignKey('ResourceClasses.ResourceClassType', ondelete='CASCADE', onupdate='CASCADE'), nullable=False)
    Staple: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=text('0'))
    Tooltip: Mapped[str] = mapped_column(Text, nullable=False)
    Tradeable: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=text('1'))
    UnlocksCiv: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=text('0'))
    Weight: Mapped[int] = mapped_column(Integer, nullable=False, server_default=text('0'))

    Civilizations_: Mapped[list['Civilizations']] = relationship('Civilizations', secondary='Resource_RequiredCivs', back_populates='Resources')
    Leaders_: Mapped[list['Leaders']] = relationship('Leaders', secondary='Resource_RequiredLeaders', back_populates='Resources')
    ResourceClasses_: Mapped['ResourceClasses'] = relationship('ResourceClasses', back_populates='Resources')
    BarbarianTribes: Mapped[list['BarbarianTribes']] = relationship('BarbarianTribes', back_populates='Resources_')
    Constructible_ValidResources: Mapped[list['ConstructibleValidResources']] = relationship('ConstructibleValidResources', back_populates='Resources_')
    Projects: Mapped[list['Projects']] = relationship('Projects', back_populates='Resources_')
    Resource_Harvests: Mapped[list['ResourceHarvests']] = relationship('ResourceHarvests', back_populates='Resources_')
    Resource_ValidAges: Mapped[list['ResourceValidAges']] = relationship('ResourceValidAges', back_populates='Resources_')
    Resource_ValidBiomes: Mapped[list['ResourceValidBiomes']] = relationship('ResourceValidBiomes', back_populates='Resources_')
    Resource_YieldChanges: Mapped[list['ResourceYieldChanges']] = relationship('ResourceYieldChanges', back_populates='Resources_')
    StartBiasResources: Mapped[list['StartBiasResources']] = relationship('StartBiasResources', back_populates='Resources_')
    Units: Mapped[list['Units']] = relationship('Units', back_populates='Resources_')
    Wonders: Mapped[list['Wonders']] = relationship('Wonders', back_populates='Resources_')
    Boosts: Mapped[list['Boosts']] = relationship('Boosts', back_populates='Resources_')
    GreatPersonIndividuals: Mapped[list['GreatPersonIndividuals']] = relationship('GreatPersonIndividuals', back_populates='Resources_')


class StartBiasAdjacentToCoasts(Base):
    __tablename__ = 'StartBiasAdjacentToCoasts'

    Score: Mapped[int] = mapped_column(Integer, nullable=False, server_default=text('0'))
    CivilizationType: Mapped[Optional[str]] = mapped_column(ForeignKey('Civilizations.CivilizationType', ondelete='CASCADE', onupdate='CASCADE'), primary_key=True, nullable=True)
    LeaderType: Mapped[Optional[str]] = mapped_column(ForeignKey('Leaders.LeaderType', ondelete='CASCADE', onupdate='CASCADE'), primary_key=True, nullable=True)

    Civilizations_: Mapped[Optional['Civilizations']] = relationship('Civilizations', back_populates='StartBiasAdjacentToCoasts')
    Leaders_: Mapped[Optional['Leaders']] = relationship('Leaders', back_populates='StartBiasAdjacentToCoasts')


class StartBiasBiomes(Base):
    __tablename__ = 'StartBiasBiomes'

    BiomeType: Mapped[str] = mapped_column(ForeignKey('Biomes.BiomeType', ondelete='CASCADE', onupdate='CASCADE'), primary_key=True)
    Score: Mapped[int] = mapped_column(Integer, nullable=False, server_default=text('0'))
    CivilizationType: Mapped[Optional[str]] = mapped_column(ForeignKey('Civilizations.CivilizationType', ondelete='CASCADE', onupdate='CASCADE'), primary_key=True, nullable=True)
    LeaderType: Mapped[Optional[str]] = mapped_column(ForeignKey('Leaders.LeaderType', ondelete='CASCADE', onupdate='CASCADE'), primary_key=True, nullable=True)

    Biomes_: Mapped['Biomes'] = relationship('Biomes', back_populates='StartBiasBiomes')
    Civilizations_: Mapped[Optional['Civilizations']] = relationship('Civilizations', back_populates='StartBiasBiomes')
    Leaders_: Mapped[Optional['Leaders']] = relationship('Leaders', back_populates='StartBiasBiomes')


class StartBiasFeatureClasses(Base):
    __tablename__ = 'StartBiasFeatureClasses'

    FeatureClassType: Mapped[str] = mapped_column(ForeignKey('FeatureClasses.FeatureClassType', ondelete='CASCADE', onupdate='CASCADE'), primary_key=True)
    Score: Mapped[int] = mapped_column(Integer, nullable=False, server_default=text('0'))
    CivilizationType: Mapped[Optional[str]] = mapped_column(ForeignKey('Civilizations.CivilizationType', ondelete='CASCADE', onupdate='CASCADE'), primary_key=True, nullable=True)
    LeaderType: Mapped[Optional[str]] = mapped_column(ForeignKey('Leaders.LeaderType', ondelete='CASCADE', onupdate='CASCADE'), primary_key=True, nullable=True)

    Civilizations_: Mapped[Optional['Civilizations']] = relationship('Civilizations', back_populates='StartBiasFeatureClasses')
    FeatureClasses_: Mapped['FeatureClasses'] = relationship('FeatureClasses', back_populates='StartBiasFeatureClasses')
    Leaders_: Mapped[Optional['Leaders']] = relationship('Leaders', back_populates='StartBiasFeatureClasses')


class StartBiasLakes(Base):
    __tablename__ = 'StartBiasLakes'

    Score: Mapped[int] = mapped_column(Integer, nullable=False, server_default=text('0'))
    CivilizationType: Mapped[Optional[str]] = mapped_column(ForeignKey('Civilizations.CivilizationType', ondelete='CASCADE', onupdate='CASCADE'), primary_key=True, nullable=True)
    LeaderType: Mapped[Optional[str]] = mapped_column(ForeignKey('Leaders.LeaderType', ondelete='CASCADE', onupdate='CASCADE'), primary_key=True, nullable=True)

    Civilizations_: Mapped[Optional['Civilizations']] = relationship('Civilizations', back_populates='StartBiasLakes')
    Leaders_: Mapped[Optional['Leaders']] = relationship('Leaders', back_populates='StartBiasLakes')


class StartBiasNaturalWonders(Base):
    __tablename__ = 'StartBiasNaturalWonders'

    Score: Mapped[int] = mapped_column(Integer, nullable=False, server_default=text('0'))
    CivilizationType: Mapped[Optional[str]] = mapped_column(ForeignKey('Civilizations.CivilizationType', ondelete='CASCADE', onupdate='CASCADE'), primary_key=True, nullable=True)
    LeaderType: Mapped[Optional[str]] = mapped_column(ForeignKey('Leaders.LeaderType', ondelete='CASCADE', onupdate='CASCADE'), primary_key=True, nullable=True)

    Civilizations_: Mapped[Optional['Civilizations']] = relationship('Civilizations', back_populates='StartBiasNaturalWonders')
    Leaders_: Mapped[Optional['Leaders']] = relationship('Leaders', back_populates='StartBiasNaturalWonders')


class StartBiasRivers(Base):
    __tablename__ = 'StartBiasRivers'

    Score: Mapped[int] = mapped_column(Integer, nullable=False, server_default=text('0'))
    CivilizationType: Mapped[Optional[str]] = mapped_column(ForeignKey('Civilizations.CivilizationType', ondelete='CASCADE', onupdate='CASCADE'), primary_key=True, nullable=True)
    LeaderType: Mapped[Optional[str]] = mapped_column(ForeignKey('Leaders.LeaderType', ondelete='CASCADE', onupdate='CASCADE'), primary_key=True, nullable=True)

    Civilizations_: Mapped[Optional['Civilizations']] = relationship('Civilizations', back_populates='StartBiasRivers')
    Leaders_: Mapped[Optional['Leaders']] = relationship('Leaders', back_populates='StartBiasRivers')


class StartBiasTerrains(Base):
    __tablename__ = 'StartBiasTerrains'

    TerrainType: Mapped[str] = mapped_column(ForeignKey('Terrains.TerrainType', ondelete='CASCADE', onupdate='CASCADE'), primary_key=True)
    Score: Mapped[int] = mapped_column(Integer, nullable=False, server_default=text('0'))
    CivilizationType: Mapped[Optional[str]] = mapped_column(ForeignKey('Civilizations.CivilizationType', ondelete='CASCADE', onupdate='CASCADE'), primary_key=True, nullable=True)
    LeaderType: Mapped[Optional[str]] = mapped_column(ForeignKey('Leaders.LeaderType', ondelete='CASCADE', onupdate='CASCADE'), primary_key=True, nullable=True)

    Civilizations_: Mapped[Optional['Civilizations']] = relationship('Civilizations', back_populates='StartBiasTerrains')
    Leaders_: Mapped[Optional['Leaders']] = relationship('Leaders', back_populates='StartBiasTerrains')
    Terrains_: Mapped['Terrains'] = relationship('Terrains', back_populates='StartBiasTerrains')


class StrategyConditions(Base):
    __tablename__ = 'StrategyConditions'

    Exclusive: Mapped[bool] = mapped_column(Boolean, primary_key=True, server_default=text('0'))
    Disqualifier: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=text('0'))
    Forbidden: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=text('0'))
    ThresholdValue: Mapped[int] = mapped_column(Integer, nullable=False, server_default=text('0'))
    ConditionFunction: Mapped[Optional[str]] = mapped_column(Text, primary_key=True, nullable=True)
    StrategyType: Mapped[Optional[str]] = mapped_column(ForeignKey('Strategies.StrategyType', ondelete='CASCADE', onupdate='CASCADE'), primary_key=True, nullable=True)
    StringValue: Mapped[Optional[str]] = mapped_column(Text, primary_key=True, nullable=True)

    Strategies_: Mapped[Optional['Strategies']] = relationship('Strategies', back_populates='StrategyConditions')


t_Strategy_Priorities = Table(
    'Strategy_Priorities', Base.metadata,
    Column('ListType', ForeignKey('AiListTypes.ListType', ondelete='CASCADE', onupdate='CASCADE'), primary_key=True),
    Column('StrategyType', ForeignKey('Strategies.StrategyType', ondelete='CASCADE', onupdate='CASCADE'), primary_key=True)
)


class StrategyYieldPriorities(Base):
    __tablename__ = 'Strategy_YieldPriorities'

    PercentageDelta: Mapped[int] = mapped_column(Integer, nullable=False, server_default=text('0'))
    PseudoYieldType: Mapped[Optional[str]] = mapped_column(ForeignKey('PseudoYields.PseudoYieldType', ondelete='CASCADE', onupdate='CASCADE'), primary_key=True, nullable=True)
    StrategyType: Mapped[Optional[str]] = mapped_column(ForeignKey('Strategies.StrategyType', ondelete='CASCADE', onupdate='CASCADE'), primary_key=True, nullable=True)
    YieldType: Mapped[Optional[str]] = mapped_column(ForeignKey('Yields.YieldType', ondelete='CASCADE', onupdate='CASCADE'), primary_key=True, nullable=True)

    PseudoYields_: Mapped[Optional['PseudoYields']] = relationship('PseudoYields', back_populates='Strategy_YieldPriorities')
    Strategies_: Mapped[Optional['Strategies']] = relationship('Strategies', back_populates='Strategy_YieldPriorities')
    Yields_: Mapped[Optional['Yields']] = relationship('Yields', back_populates='Strategy_YieldPriorities')


class Traditions(Base):
    __tablename__ = 'Traditions'

    TraditionType: Mapped[str] = mapped_column(Text, primary_key=True)
    IsCrisis: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=text('0'))
    Name: Mapped[str] = mapped_column(Text, nullable=False)
    OnlyLegacyCivTrait: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=text('0'))
    UseLegacyTraits: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=text('1'))
    AgeType: Mapped[Optional[str]] = mapped_column(ForeignKey('Ages.AgeType', ondelete='CASCADE', onupdate='CASCADE'))
    Description: Mapped[Optional[str]] = mapped_column(Text)
    ObsoletesTraditionType: Mapped[Optional[str]] = mapped_column(Text)
    TraitType: Mapped[Optional[str]] = mapped_column(ForeignKey('Traits.TraitType', ondelete='SET DEFAULT', onupdate='SET DEFAULT'))

    Attributes_: Mapped[list['Attributes']] = relationship('Attributes', secondary='TraditionAttributes', back_populates='Traditions')
    Modifiers_: Mapped[list['Modifiers']] = relationship('Modifiers', secondary='TraditionModifiers', back_populates='Traditions')
    Ages_: Mapped[Optional['Ages']] = relationship('Ages', back_populates='Traditions')
    Traits_: Mapped[Optional['Traits']] = relationship('Traits', back_populates='Traditions')


t_TraitModifiers = Table(
    'TraitModifiers', Base.metadata,
    Column('ModifierId', ForeignKey('Modifiers.ModifierId', ondelete='CASCADE', onupdate='CASCADE'), primary_key=True),
    Column('TraitType', ForeignKey('Traits.TraitType', ondelete='CASCADE', onupdate='CASCADE'), primary_key=True)
)


class UnitDiplomacyActionTargets(Base):
    __tablename__ = 'UnitDiplomacyAction_Targets'

    DiplomacyActionType: Mapped[str] = mapped_column(ForeignKey('DiplomacyActions.DiplomacyActionType', ondelete='CASCADE', onupdate='CASCADE'), primary_key=True)
    TargetSpace: Mapped[str] = mapped_column(Text, primary_key=True)
    UnitTag: Mapped[str] = mapped_column(ForeignKey('Tags.Tag', ondelete='CASCADE', onupdate='CASCADE'), primary_key=True)
    CivilizationLevelType: Mapped[str] = mapped_column(ForeignKey('CivilizationLevels.CivilizationLevelType', ondelete='SET DEFAULT', onupdate='CASCADE'), nullable=False)

    CivilizationLevels_: Mapped['CivilizationLevels'] = relationship('CivilizationLevels', back_populates='UnitDiplomacyAction_Targets')
    DiplomacyActions_: Mapped['DiplomacyActions'] = relationship('DiplomacyActions', back_populates='UnitDiplomacyAction_Targets')
    Tags_: Mapped['Tags'] = relationship('Tags', back_populates='UnitDiplomacyAction_Targets')


t_UnitDiplomacyAction_ValidUnits = Table(
    'UnitDiplomacyAction_ValidUnits', Base.metadata,
    Column('DiplomacyActionType', ForeignKey('DiplomacyActions.DiplomacyActionType', ondelete='CASCADE', onupdate='CASCADE'), primary_key=True),
    Column('UnitTag', ForeignKey('Tags.Tag', ondelete='CASCADE', onupdate='CASCADE'), primary_key=True)
)


class UnitOperations(Base):
    __tablename__ = 'UnitOperations'

    OperationType: Mapped[str] = mapped_column(Text, primary_key=True)
    BaseProbability: Mapped[int] = mapped_column(Integer, nullable=False, server_default=text('0'))
    Description: Mapped[str] = mapped_column(Text, nullable=False)
    EnemyLevelProbChange: Mapped[int] = mapped_column(Integer, nullable=False, server_default=text('0'))
    EnemyProbChange: Mapped[int] = mapped_column(Integer, nullable=False, server_default=text('0'))
    HoldCycling: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=text('0'))
    Icon: Mapped[str] = mapped_column(Text, nullable=False)
    LevelProbChange: Mapped[int] = mapped_column(Integer, nullable=False, server_default=text('0'))
    Name: Mapped[str] = mapped_column(Text, nullable=False)
    Offensive: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=text('0'))
    RequiresAbility: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=text('0'))
    ShowActivationPlots: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=text('0'))
    Turns: Mapped[int] = mapped_column(Integer, nullable=False, server_default=text('0'))
    VisibleInUI: Mapped[bool] = mapped_column(Boolean, nullable=False)
    CategoryInUI: Mapped[Optional[str]] = mapped_column(Text)
    DisabledHelp: Mapped[Optional[str]] = mapped_column(Text)
    Help: Mapped[Optional[str]] = mapped_column(Text)
    HotkeyId: Mapped[Optional[str]] = mapped_column(Text)
    InterfaceMode: Mapped[Optional[str]] = mapped_column(ForeignKey('InterfaceModes.InterfaceModeType', ondelete='CASCADE', onupdate='CASCADE'))
    PriorityInUI: Mapped[Optional[int]] = mapped_column(Integer)
    Sound: Mapped[Optional[str]] = mapped_column(Text)
    TargetDistrict: Mapped[Optional[str]] = mapped_column(ForeignKey('Districts.DistrictType', ondelete='CASCADE', onupdate='CASCADE'))

    InterfaceModes_: Mapped[Optional['InterfaceModes']] = relationship('InterfaceModes', back_populates='UnitOperations')
    Districts_: Mapped[Optional['Districts']] = relationship('Districts', back_populates='UnitOperations')
    UnitAbilities: Mapped[list['UnitAbilities']] = relationship('UnitAbilities', back_populates='UnitOperations_')
    AIUnitPrioritizedActions: Mapped[list['AIUnitPrioritizedActions']] = relationship('AIUnitPrioritizedActions', back_populates='UnitOperations_')


t_UnitPromotionClassSets = Table(
    'UnitPromotionClassSets', Base.metadata,
    Column('PromotionClassType', ForeignKey('UnitPromotionClasses.PromotionClassType', ondelete='CASCADE', onupdate='CASCADE'), primary_key=True),
    Column('UnitPromotionDisciplineType', ForeignKey('UnitPromotionDisciplines.UnitPromotionDisciplineType', ondelete='CASCADE', onupdate='CASCADE'), primary_key=True)
)


class UnitPromotionDisciplineDetails(Base):
    __tablename__ = 'UnitPromotionDisciplineDetails'

    UnitPromotionDisciplineType: Mapped[str] = mapped_column(ForeignKey('UnitPromotionDisciplines.UnitPromotionDisciplineType', ondelete='CASCADE', onupdate='CASCADE'), primary_key=True)
    UnitPromotionType: Mapped[str] = mapped_column(ForeignKey('UnitPromotions.UnitPromotionType', ondelete='CASCADE', onupdate='CASCADE'), primary_key=True)
    GrantsCommendation: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=text('0'))
    PrereqUnitPromotion: Mapped[Optional[str]] = mapped_column(ForeignKey('UnitPromotions.UnitPromotionType', ondelete='CASCADE', onupdate='CASCADE'), primary_key=True, nullable=True)
    GrantCommendationWithAnyPrereq: Mapped[Optional[bool]] = mapped_column(Boolean, server_default=text('0'))

    UnitPromotions_: Mapped[Optional['UnitPromotions']] = relationship('UnitPromotions', foreign_keys=[PrereqUnitPromotion], back_populates='UnitPromotionDisciplineDetails')
    UnitPromotionDisciplines_: Mapped['UnitPromotionDisciplines'] = relationship('UnitPromotionDisciplines', back_populates='UnitPromotionDisciplineDetails')
    UnitPromotions1: Mapped['UnitPromotions'] = relationship('UnitPromotions', foreign_keys=[UnitPromotionType], back_populates='UnitPromotionDisciplineDetails_')


t_UnitPromotionModifiers = Table(
    'UnitPromotionModifiers', Base.metadata,
    Column('ModifierId', ForeignKey('Modifiers.ModifierId', ondelete='CASCADE', onupdate='CASCADE'), primary_key=True),
    Column('UnitPromotionType', ForeignKey('UnitPromotions.UnitPromotionType', ondelete='CASCADE', onupdate='CASCADE'), primary_key=True)
)


class UnlockConfigurationValues(Base):
    __tablename__ = 'UnlockConfigurationValues'

    UnlockType: Mapped[str] = mapped_column(ForeignKey('Unlocks.UnlockType', ondelete='CASCADE', onupdate='CASCADE'), primary_key=True)
    ConfigurationValue: Mapped[str] = mapped_column(Text, nullable=False)


class UnlockRequirements(Base):
    __tablename__ = 'UnlockRequirements'

    RequirementSetId: Mapped[str] = mapped_column(ForeignKey('RequirementSets.RequirementSetId', ondelete='CASCADE', onupdate='CASCADE'), primary_key=True)
    UnlockType: Mapped[str] = mapped_column(ForeignKey('Unlocks.UnlockType', ondelete='CASCADE', onupdate='CASCADE'), primary_key=True)
    Description: Mapped[Optional[str]] = mapped_column(Text)
    NarrativeText: Mapped[Optional[str]] = mapped_column(Text)
    ToolTip: Mapped[Optional[str]] = mapped_column(Text)

    RequirementSets_: Mapped['RequirementSets'] = relationship('RequirementSets', back_populates='UnlockRequirements')
    Unlocks_: Mapped['Unlocks'] = relationship('Unlocks', back_populates='UnlockRequirements')


class VisArtCivilizationBuildingCultures(Base):
    __tablename__ = 'VisArt_CivilizationBuildingCultures'

    BuildingCulture: Mapped[str] = mapped_column(Text, primary_key=True)
    CivilizationType: Mapped[str] = mapped_column(ForeignKey('Civilizations.CivilizationType', ondelete='CASCADE', onupdate='CASCADE'), primary_key=True)

    Civilizations_: Mapped['Civilizations'] = relationship('Civilizations', back_populates='VisArt_CivilizationBuildingCultures')


class VisArtCivilizationUnitCultures(Base):
    __tablename__ = 'VisArt_CivilizationUnitCultures'

    CivilizationType: Mapped[str] = mapped_column(ForeignKey('Civilizations.CivilizationType', ondelete='CASCADE', onupdate='CASCADE'), primary_key=True)
    UnitCulture: Mapped[str] = mapped_column(Text, primary_key=True)

    Civilizations_: Mapped['Civilizations'] = relationship('Civilizations', back_populates='VisArt_CivilizationUnitCultures')


class AdjacencyYieldChanges(Base):
    __tablename__ = 'Adjacency_YieldChanges'

    ID: Mapped[str] = mapped_column(Text, primary_key=True)
    AdjacentLake: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=text('0'))
    AdjacentNaturalWonder: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=text('0'))
    AdjacentNavigableRiver: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=text('0'))
    AdjacentQuarter: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=text('0'))
    AdjacentResource: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=text('0'))
    AdjacentResourceClass: Mapped[str] = mapped_column(Text, nullable=False, server_default=text('"NO_RESOURCECLASS"'))
    AdjacentRiver: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=text('0'))
    AdjacentSeaResource: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=text('0'))
    AdjacentUniqueQuarter: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=text('0'))
    ProjectMaxYield: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=text('0'))
    Self: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=text('0'))
    TilesRequired: Mapped[int] = mapped_column(Integer, nullable=False, server_default=text('1'))
    YieldChange: Mapped[float] = mapped_column(REAL, nullable=False, server_default=text('0'))
    YieldType: Mapped[str] = mapped_column(ForeignKey('Yields.YieldType', ondelete='CASCADE', onupdate='CASCADE'), nullable=False)
    AdjacentBiome: Mapped[Optional[str]] = mapped_column(ForeignKey('Biomes.BiomeType', ondelete='CASCADE', onupdate='CASCADE'))
    AdjacentConstructible: Mapped[Optional[str]] = mapped_column(ForeignKey('Constructibles.ConstructibleType', ondelete='CASCADE', onupdate='CASCADE'))
    AdjacentConstructibleTag: Mapped[Optional[str]] = mapped_column(Text)
    AdjacentDistrict: Mapped[Optional[str]] = mapped_column(ForeignKey('Districts.DistrictType', ondelete='CASCADE', onupdate='CASCADE'))
    AdjacentFeature: Mapped[Optional[str]] = mapped_column(ForeignKey('Features.FeatureType', ondelete='CASCADE', onupdate='CASCADE'))
    AdjacentFeatureClass: Mapped[Optional[str]] = mapped_column(Text)
    AdjacentTerrain: Mapped[Optional[str]] = mapped_column(ForeignKey('Terrains.TerrainType', ondelete='CASCADE', onupdate='CASCADE'))
    AdjacentUniqueQuarterType: Mapped[Optional[str]] = mapped_column(Text)
    Age: Mapped[Optional[str]] = mapped_column(Text)

    Traits_: Mapped[list['Traits']] = relationship('Traits', secondary='ExcludedAdjacencies', back_populates='Adjacency_YieldChanges')
    Biomes_: Mapped[Optional['Biomes']] = relationship('Biomes', back_populates='Adjacency_YieldChanges')
    Constructibles_: Mapped[Optional['Constructibles']] = relationship('Constructibles', back_populates='Adjacency_YieldChanges')
    Districts_: Mapped[Optional['Districts']] = relationship('Districts', back_populates='Adjacency_YieldChanges')
    Features_: Mapped[Optional['Features']] = relationship('Features', back_populates='Adjacency_YieldChanges')
    Terrains_: Mapped[Optional['Terrains']] = relationship('Terrains', back_populates='Adjacency_YieldChanges')
    Yields_: Mapped['Yields'] = relationship('Yields', back_populates='Adjacency_YieldChanges')
    Constructible_Adjacencies: Mapped[list['ConstructibleAdjacencies']] = relationship('ConstructibleAdjacencies', back_populates='Adjacency_YieldChanges')


class BarbarianTribes(Base):
    __tablename__ = 'BarbarianTribes'

    TribeType: Mapped[str] = mapped_column(Text, primary_key=True)
    CityAttackBoldness: Mapped[int] = mapped_column(Integer, nullable=False, server_default=text('25'))
    CityAttackOperation: Mapped[str] = mapped_column(Text, nullable=False)
    DefenderTag: Mapped[str] = mapped_column(Text, nullable=False)
    IsCoastal: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=text('0'))
    MeleeTag: Mapped[str] = mapped_column(Text, nullable=False)
    PercentRangedUnits: Mapped[int] = mapped_column(Integer, nullable=False, server_default=text('0'))
    RaidingBehaviorTree: Mapped[str] = mapped_column(Text, nullable=False)
    RaidingBoldness: Mapped[int] = mapped_column(Integer, nullable=False, server_default=text('20'))
    RangedTag: Mapped[str] = mapped_column(Text, nullable=False)
    ResourceRange: Mapped[int] = mapped_column(Integer, nullable=False, server_default=text('0'))
    ScoutingBehaviorTree: Mapped[str] = mapped_column(Text, nullable=False)
    ScoutTag: Mapped[str] = mapped_column(Text, nullable=False)
    SiegeTag: Mapped[str] = mapped_column(Text, nullable=False)
    TurnsToWarriorSpawn: Mapped[int] = mapped_column(Integer, nullable=False, server_default=text('15'))
    RequiredResource: Mapped[Optional[str]] = mapped_column(ForeignKey('Resources.ResourceType', ondelete='CASCADE', onupdate='CASCADE'))
    SupportTag: Mapped[Optional[str]] = mapped_column(Text)

    Resources_: Mapped[Optional['Resources']] = relationship('Resources', back_populates='BarbarianTribes')
    BarbarianTribeNames: Mapped[list['BarbarianTribeNames']] = relationship('BarbarianTribeNames', back_populates='BarbarianTribes_')
    BarbarianTribeForces: Mapped[list['BarbarianTribeForces']] = relationship('BarbarianTribeForces', back_populates='BarbarianTribes_')


class Buildings(Base):
    __tablename__ = 'Buildings'

    ConstructibleType: Mapped[str] = mapped_column(ForeignKey('Constructibles.ConstructibleType', ondelete='CASCADE', onupdate='CASCADE'), primary_key=True)
    AllowsHolyCity: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=text('0'))
    ArchaeologyResearch: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=text('0'))
    BuildQueue: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=text('0'))
    Capital: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=text('0'))
    CityCenterPriority: Mapped[int] = mapped_column(Integer, nullable=False, server_default=text('0'))
    DefenseModifier: Mapped[int] = mapped_column(Integer, nullable=False, server_default=text('0'))
    GrantFortification: Mapped[int] = mapped_column(Integer, nullable=False, server_default=text('0'))
    Housing: Mapped[int] = mapped_column(Integer, nullable=False, server_default=text('0'))
    MaxPlayerInstances: Mapped[int] = mapped_column(Integer, nullable=False, server_default=text('-1'))
    Movable: Mapped[bool] = mapped_column(Boolean, nullable=False)
    MultiplePerCity: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=text('0'))
    MustPurchase: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=text('0'))
    OuterDefenseStrength: Mapped[int] = mapped_column(Integer, nullable=False, server_default=text('0'))
    Purchasable: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=text('1'))
    Town: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=text('0'))
    Workable: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=text('0'))
    CitizenSlots: Mapped[Optional[int]] = mapped_column(Integer)
    OuterDefenseHitPoints: Mapped[Optional[int]] = mapped_column(Integer)
    PurchaseYield: Mapped[Optional[str]] = mapped_column(ForeignKey('Yields.YieldType', ondelete='SET DEFAULT', onupdate='SET DEFAULT'))
    TraitType: Mapped[Optional[str]] = mapped_column(ForeignKey('Traits.TraitType', ondelete='SET DEFAULT', onupdate='SET DEFAULT'))

    Yields_: Mapped[Optional['Yields']] = relationship('Yields', back_populates='Buildings')
    Traits_: Mapped[Optional['Traits']] = relationship('Traits', back_populates='Buildings')


class ChargedUnitAbilities(Base):
    __tablename__ = 'ChargedUnitAbilities'

    UnitAbilityType: Mapped[str] = mapped_column(Text, primary_key=True)
    RechargeTurns: Mapped[int] = mapped_column(Integer, nullable=False, server_default=text('-1'))
    ConstructibleType: Mapped[Optional[str]] = mapped_column(ForeignKey('Constructibles.ConstructibleType', ondelete='CASCADE', onupdate='CASCADE'))

    Constructibles_: Mapped[Optional['Constructibles']] = relationship('Constructibles', back_populates='ChargedUnitAbilities')
    AIUnitPrioritizedActions: Mapped[list['AIUnitPrioritizedActions']] = relationship('AIUnitPrioritizedActions', back_populates='ChargedUnitAbilities_')


t_Constructible_Advisories = Table(
    'Constructible_Advisories', Base.metadata,
    Column('AdvisoryClassType', ForeignKey('AdvisoryClasses.AdvisoryClassType', ondelete='CASCADE', onupdate='CASCADE'), primary_key=True),
    Column('ConstructibleType', ForeignKey('Constructibles.ConstructibleType', ondelete='CASCADE', onupdate='CASCADE'), primary_key=True)
)


class ConstructibleAttributePoints(Base):
    __tablename__ = 'Constructible_AttributePoints'

    AttributeType: Mapped[str] = mapped_column(ForeignKey('Attributes.AttributeType', ondelete='CASCADE', onupdate='CASCADE'), primary_key=True)
    ConstructibleType: Mapped[str] = mapped_column(ForeignKey('Constructibles.ConstructibleType', ondelete='CASCADE', onupdate='CASCADE'), primary_key=True)
    Points: Mapped[float] = mapped_column(REAL, nullable=False, server_default=text('0.0'))

    Attributes_: Mapped['Attributes'] = relationship('Attributes', back_populates='Constructible_AttributePoints')
    Constructibles_: Mapped['Constructibles'] = relationship('Constructibles', back_populates='Constructible_AttributePoints')


class ConstructibleBuildingCostProgressions(Base):
    __tablename__ = 'Constructible_BuildingCostProgressions'

    ConstructibleType: Mapped[str] = mapped_column(ForeignKey('Constructibles.ConstructibleType', ondelete='CASCADE', onupdate='CASCADE'), primary_key=True)
    Percent: Mapped[int] = mapped_column(Integer, nullable=False, server_default=text('0'))


class ConstructibleCitizenYieldChanges(Base):
    __tablename__ = 'Constructible_CitizenYieldChanges'

    ConstructibleType: Mapped[str] = mapped_column(ForeignKey('Constructibles.ConstructibleType', ondelete='CASCADE', onupdate='CASCADE'), primary_key=True)
    YieldType: Mapped[str] = mapped_column(ForeignKey('Yields.YieldType', ondelete='CASCADE', onupdate='CASCADE'), primary_key=True)
    YieldChange: Mapped[int] = mapped_column(Integer, nullable=False)

    Constructibles_: Mapped['Constructibles'] = relationship('Constructibles', back_populates='Constructible_CitizenYieldChanges')
    Yields_: Mapped['Yields'] = relationship('Yields', back_populates='Constructible_CitizenYieldChanges')


class ConstructibleGreatWorks(Base):
    __tablename__ = 'Constructible_GreatWorks'

    ConstructibleType: Mapped[str] = mapped_column(ForeignKey('Constructibles.ConstructibleType', ondelete='CASCADE', onupdate='CASCADE'), primary_key=True)
    GreatWorkSlotType: Mapped[str] = mapped_column(ForeignKey('GreatWorkSlotTypes.GreatWorkSlotType', ondelete='CASCADE', onupdate='CASCADE'), primary_key=True)
    NonUniquePersonYield: Mapped[int] = mapped_column(Integer, nullable=False, server_default=text('0'))
    NumSlots: Mapped[int] = mapped_column(Integer, nullable=False, server_default=text('1'))
    ThemingSameAges: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=text('0'))
    ThemingSameObjectType: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=text('0'))
    ThemingUniqueCivs: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=text('0'))
    ThemingUniquePerson: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=text('0'))
    ThemingYieldMultiplier: Mapped[int] = mapped_column(Integer, nullable=False, server_default=text('0'))
    ThemingBonusDescription: Mapped[Optional[str]] = mapped_column(Text)

    Constructibles_: Mapped['Constructibles'] = relationship('Constructibles', back_populates='Constructible_GreatWorks')
    GreatWorkSlotTypes_: Mapped['GreatWorkSlotTypes'] = relationship('GreatWorkSlotTypes', back_populates='Constructible_GreatWorks')


t_Constructible_InvalidAdjacentBiomes = Table(
    'Constructible_InvalidAdjacentBiomes', Base.metadata,
    Column('BiomeType', ForeignKey('Biomes.BiomeType', ondelete='CASCADE', onupdate='CASCADE'), primary_key=True),
    Column('ConstructibleType', ForeignKey('Constructibles.ConstructibleType', ondelete='CASCADE', onupdate='CASCADE'), primary_key=True)
)


t_Constructible_InvalidFeatures = Table(
    'Constructible_InvalidFeatures', Base.metadata,
    Column('ConstructibleType', ForeignKey('Constructibles.ConstructibleType', ondelete='CASCADE', onupdate='CASCADE'), primary_key=True),
    Column('FeatureType', ForeignKey('Features.FeatureType', ondelete='CASCADE', onupdate='CASCADE'), primary_key=True)
)


class ConstructibleLogistics(Base):
    __tablename__ = 'Constructible_Logistics'

    ConstructibleType: Mapped[str] = mapped_column(ForeignKey('Constructibles.ConstructibleType', ondelete='CASCADE', onupdate='CASCADE'), primary_key=True)
    BuildChargeCost: Mapped[int] = mapped_column(Integer, nullable=False, server_default=text('1'))
    CombatStrength: Mapped[int] = mapped_column(Integer, nullable=False, server_default=text('0'))
    MaxHealPerTurn: Mapped[int] = mapped_column(Integer, nullable=False)
    PlotOwned: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=text('0'))
    PlotWallsDefense: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=text('0'))
    Supplies: Mapped[int] = mapped_column(Integer, nullable=False, server_default=text('0'))


class ConstructibleMaintenances(Base):
    __tablename__ = 'Constructible_Maintenances'

    ConstructibleType: Mapped[str] = mapped_column(ForeignKey('Constructibles.ConstructibleType', ondelete='CASCADE', onupdate='CASCADE'), primary_key=True)
    YieldType: Mapped[str] = mapped_column(ForeignKey('Yields.YieldType', ondelete='CASCADE', onupdate='CASCADE'), primary_key=True)
    Amount: Mapped[int] = mapped_column(Integer, nullable=False)

    Constructibles_: Mapped['Constructibles'] = relationship('Constructibles', back_populates='Constructible_Maintenances')
    Yields_: Mapped['Yields'] = relationship('Yields', back_populates='Constructible_Maintenances')


class ConstructiblePillageRandomEvents(Base):
    __tablename__ = 'Constructible_PillageRandomEvents'

    ConstructibleType: Mapped[str] = mapped_column(ForeignKey('Constructibles.ConstructibleType', ondelete='CASCADE', onupdate='CASCADE'), primary_key=True)
    EventClass: Mapped[str] = mapped_column(Text, primary_key=True)
    PercentChance: Mapped[int] = mapped_column(Integer, nullable=False, server_default=text('0'))

    Constructibles_: Mapped['Constructibles'] = relationship('Constructibles', back_populates='Constructible_PillageRandomEvents')


class ConstructiblePlunders(Base):
    __tablename__ = 'Constructible_Plunders'

    ConstructibleType: Mapped[str] = mapped_column(ForeignKey('Constructibles.ConstructibleType', ondelete='CASCADE', onupdate='CASCADE'), primary_key=True)
    PlunderType: Mapped[str] = mapped_column(ForeignKey('Plunders.PlunderType', ondelete='CASCADE', onupdate='CASCADE'), primary_key=True)
    Amount: Mapped[int] = mapped_column(Integer, nullable=False, server_default=text('0'))

    Constructibles_: Mapped['Constructibles'] = relationship('Constructibles', back_populates='Constructible_Plunders')
    Plunders_: Mapped['Plunders'] = relationship('Plunders', back_populates='Constructible_Plunders')


t_Constructible_RequiredFeatureClasses = Table(
    'Constructible_RequiredFeatureClasses', Base.metadata,
    Column('ConstructibleType', ForeignKey('Constructibles.ConstructibleType', ondelete='CASCADE', onupdate='CASCADE'), primary_key=True),
    Column('FeatureClassType', ForeignKey('FeatureClasses.FeatureClassType', ondelete='CASCADE', onupdate='CASCADE'), primary_key=True)
)


t_Constructible_RequiredFeatures = Table(
    'Constructible_RequiredFeatures', Base.metadata,
    Column('ConstructibleType', ForeignKey('Constructibles.ConstructibleType', ondelete='CASCADE', onupdate='CASCADE'), primary_key=True),
    Column('FeatureType', ForeignKey('Features.FeatureType', ondelete='CASCADE', onupdate='CASCADE'), primary_key=True)
)


class ConstructibleTransitionRemoves(Base):
    __tablename__ = 'Constructible_TransitionRemoves'

    ConstructibleType: Mapped[str] = mapped_column(ForeignKey('Constructibles.ConstructibleType', ondelete='CASCADE', onupdate='CASCADE'), primary_key=True)


t_Constructible_ValidBiomes = Table(
    'Constructible_ValidBiomes', Base.metadata,
    Column('BiomeType', ForeignKey('Biomes.BiomeType', ondelete='CASCADE', onupdate='CASCADE'), primary_key=True),
    Column('ConstructibleType', ForeignKey('Constructibles.ConstructibleType', ondelete='CASCADE', onupdate='CASCADE'), primary_key=True)
)


t_Constructible_ValidDistricts = Table(
    'Constructible_ValidDistricts', Base.metadata,
    Column('ConstructibleType', ForeignKey('Constructibles.ConstructibleType', ondelete='CASCADE', onupdate='CASCADE'), primary_key=True),
    Column('DistrictType', ForeignKey('Districts.DistrictType', ondelete='CASCADE', onupdate='CASCADE'), primary_key=True)
)


t_Constructible_ValidFeatures = Table(
    'Constructible_ValidFeatures', Base.metadata,
    Column('ConstructibleType', ForeignKey('Constructibles.ConstructibleType', ondelete='CASCADE', onupdate='CASCADE'), primary_key=True),
    Column('FeatureType', ForeignKey('Features.FeatureType', ondelete='CASCADE', onupdate='CASCADE'), primary_key=True)
)


class ConstructibleValidResources(Base):
    __tablename__ = 'Constructible_ValidResources'

    ConstructibleType: Mapped[str] = mapped_column(ForeignKey('Constructibles.ConstructibleType', ondelete='CASCADE', onupdate='CASCADE'), primary_key=True)
    ResourceType: Mapped[str] = mapped_column(ForeignKey('Resources.ResourceType', ondelete='CASCADE', onupdate='CASCADE'), primary_key=True)
    Rate: Mapped[int] = mapped_column(Integer, nullable=False, server_default=text('1'))

    Constructibles_: Mapped['Constructibles'] = relationship('Constructibles', back_populates='Constructible_ValidResources')
    Resources_: Mapped['Resources'] = relationship('Resources', back_populates='Constructible_ValidResources')


t_Constructible_ValidTerrains = Table(
    'Constructible_ValidTerrains', Base.metadata,
    Column('ConstructibleType', ForeignKey('Constructibles.ConstructibleType', ondelete='CASCADE', onupdate='CASCADE'), primary_key=True),
    Column('TerrainType', ForeignKey('Terrains.TerrainType', ondelete='CASCADE', onupdate='CASCADE'), primary_key=True)
)


class ConstructibleYieldChanges(Base):
    __tablename__ = 'Constructible_YieldChanges'

    ConstructibleType: Mapped[str] = mapped_column(ForeignKey('Constructibles.ConstructibleType', ondelete='CASCADE', onupdate='CASCADE'), primary_key=True)
    YieldType: Mapped[str] = mapped_column(ForeignKey('Yields.YieldType', ondelete='CASCADE', onupdate='CASCADE'), primary_key=True)
    YieldChange: Mapped[int] = mapped_column(Integer, nullable=False)

    Constructibles_: Mapped['Constructibles'] = relationship('Constructibles', back_populates='Constructible_YieldChanges')
    Yields_: Mapped['Yields'] = relationship('Yields', back_populates='Constructible_YieldChanges')


t_District_FreeConstructibles = Table(
    'District_FreeConstructibles', Base.metadata,
    Column('BiomeType', ForeignKey('Biomes.BiomeType', ondelete='CASCADE', onupdate='CASCADE')),
    Column('ConstructibleType', ForeignKey('Constructibles.ConstructibleType', ondelete='CASCADE', onupdate='CASCADE'), nullable=False),
    Column('DistrictType', ForeignKey('Districts.DistrictType', ondelete='CASCADE', onupdate='CASCADE'), nullable=False),
    Column('FeatureType', ForeignKey('Features.FeatureType', ondelete='CASCADE', onupdate='CASCADE')),
    Column('Priority', Integer, nullable=False, server_default=text('1')),
    Column('ResourceType', ForeignKey('Resources.ResourceType', ondelete='CASCADE', onupdate='CASCADE')),
    Column('RiverType', Text),
    Column('TerrainType', ForeignKey('Terrains.TerrainType', ondelete='CASCADE', onupdate='CASCADE')),
    Column('Tier', Integer, nullable=False, server_default=text('1'))
)


t_District_RemovedFeatures = Table(
    'District_RemovedFeatures', Base.metadata,
    Column('DistrictType', ForeignKey('Districts.DistrictType', ondelete='CASCADE', onupdate='CASCADE'), nullable=False),
    Column('FeatureType', ForeignKey('Features.FeatureType', ondelete='CASCADE', onupdate='CASCADE'))
)


class EnterStageModifiers(Base):
    __tablename__ = 'EnterStageModifiers'

    ModifierId: Mapped[str] = mapped_column(ForeignKey('Modifiers.ModifierId', ondelete='CASCADE', onupdate='CASCADE'), primary_key=True)
    StageType: Mapped[str] = mapped_column(ForeignKey('DiplomaticActionStages.StageType', ondelete='CASCADE', onupdate='CASCADE'), primary_key=True)
    OneShot: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=text('0'))

    Modifiers_: Mapped['Modifiers'] = relationship('Modifiers', back_populates='EnterStageModifiers')
    DiplomaticActionStages_: Mapped['DiplomaticActionStages'] = relationship('DiplomaticActionStages', back_populates='EnterStageModifiers')


class EnvoysInStageModifiers(Base):
    __tablename__ = 'EnvoysInStageModifiers'

    ModifierId: Mapped[str] = mapped_column(ForeignKey('Modifiers.ModifierId', ondelete='CASCADE', onupdate='CASCADE'), primary_key=True)
    StageType: Mapped[str] = mapped_column(ForeignKey('DiplomaticActionStages.StageType', ondelete='CASCADE', onupdate='CASCADE'), primary_key=True)
    NumEnvoys: Mapped[int] = mapped_column(Integer, nullable=False, server_default=text('0'))

    Modifiers_: Mapped['Modifiers'] = relationship('Modifiers', back_populates='EnvoysInStageModifiers')
    DiplomaticActionStages_: Mapped['DiplomaticActionStages'] = relationship('DiplomaticActionStages', back_populates='EnvoysInStageModifiers')


t_Feature_AdjacentFeatures = Table(
    'Feature_AdjacentFeatures', Base.metadata,
    Column('FeatureType', ForeignKey('Features.FeatureType', ondelete='CASCADE', onupdate='CASCADE'), primary_key=True),
    Column('FeatureTypeAdjacent', ForeignKey('Features.FeatureType', ondelete='CASCADE', onupdate='CASCADE'), primary_key=True)
)


t_Feature_AdjacentTerrains = Table(
    'Feature_AdjacentTerrains', Base.metadata,
    Column('FeatureType', ForeignKey('Features.FeatureType', ondelete='CASCADE', onupdate='CASCADE'), primary_key=True),
    Column('TerrainType', ForeignKey('Terrains.TerrainType', ondelete='CASCADE', onupdate='CASCADE'), primary_key=True)
)


class FeatureCityYields(Base):
    __tablename__ = 'Feature_CityYields'

    Feature_CityYieldType: Mapped[str] = mapped_column(Text, primary_key=True)
    Biome: Mapped[str] = mapped_column(Text, nullable=False, server_default=text('"NO_BIOME"'))
    FeatureClass: Mapped[str] = mapped_column(Text, nullable=False, server_default=text('"NO_FEATURE_CLASS"'))
    FeatureType: Mapped[str] = mapped_column(ForeignKey('Features.FeatureType', ondelete='CASCADE', onupdate='CASCADE'), nullable=False)
    Terrain: Mapped[str] = mapped_column(Text, nullable=False, server_default=text('"NO_TERRAIN"'))
    YieldChange: Mapped[int] = mapped_column(Integer, nullable=False)
    YieldType: Mapped[str] = mapped_column(ForeignKey('Yields.YieldType', ondelete='CASCADE', onupdate='CASCADE'), nullable=False)

    Features_: Mapped['Features'] = relationship('Features', back_populates='Feature_CityYields')
    Yields_: Mapped['Yields'] = relationship('Yields', back_populates='Feature_CityYields')


class FeatureNaturalWonders(Base):
    __tablename__ = 'Feature_NaturalWonders'

    FeatureType: Mapped[str] = mapped_column(ForeignKey('Features.FeatureType', ondelete='CASCADE', onupdate='CASCADE'), primary_key=True)
    Direction: Mapped[int] = mapped_column(Integer, nullable=False, server_default=text('-1'))
    NoRiver: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=text('1'))
    PlaceFirst: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=text('0'))
    PlacementPercentage: Mapped[int] = mapped_column(Integer, nullable=False, server_default=text('0'))
    Tiles: Mapped[int] = mapped_column(Integer, nullable=False, server_default=text('0'))


t_Feature_NotAdjacentTerrains = Table(
    'Feature_NotAdjacentTerrains', Base.metadata,
    Column('FeatureType', ForeignKey('Features.FeatureType', ondelete='CASCADE', onupdate='CASCADE'), primary_key=True),
    Column('TerrainType', ForeignKey('Terrains.TerrainType', ondelete='CASCADE', onupdate='CASCADE'), primary_key=True)
)


t_Feature_NotNearFeatures = Table(
    'Feature_NotNearFeatures', Base.metadata,
    Column('FeatureType', ForeignKey('Features.FeatureType', ondelete='CASCADE', onupdate='CASCADE'), primary_key=True),
    Column('FeatureTypeAvoid', ForeignKey('Features.FeatureType', ondelete='CASCADE', onupdate='CASCADE'), primary_key=True)
)


class FeatureRemoves(Base):
    __tablename__ = 'Feature_Removes'

    FeatureType: Mapped[str] = mapped_column(ForeignKey('Features.FeatureType', ondelete='CASCADE', onupdate='CASCADE'), primary_key=True)
    YieldType: Mapped[str] = mapped_column(ForeignKey('Yields.YieldType', ondelete='CASCADE', onupdate='CASCADE'), primary_key=True)
    Yield: Mapped[int] = mapped_column(Integer, nullable=False, server_default=text('0'))

    Features_: Mapped['Features'] = relationship('Features', back_populates='Feature_Removes')
    Yields_: Mapped['Yields'] = relationship('Yields', back_populates='Feature_Removes')


class FeatureValidBiomes(Base):
    __tablename__ = 'Feature_ValidBiomes'

    BiomeType: Mapped[str] = mapped_column(ForeignKey('Biomes.BiomeType', ondelete='CASCADE', onupdate='CASCADE'), primary_key=True)
    FeatureType: Mapped[str] = mapped_column(ForeignKey('Features.FeatureType', ondelete='CASCADE', onupdate='CASCADE'), primary_key=True)
    ReplaceRange: Mapped[Optional[int]] = mapped_column(Integer)
    ReplaceWithBiomeType: Mapped[Optional[str]] = mapped_column(ForeignKey('Biomes.BiomeType', ondelete='CASCADE', onupdate='CASCADE'))

    Biomes_: Mapped['Biomes'] = relationship('Biomes', foreign_keys=[BiomeType], back_populates='Feature_ValidBiomes')
    Features_: Mapped['Features'] = relationship('Features', back_populates='Feature_ValidBiomes')
    Biomes1: Mapped[Optional['Biomes']] = relationship('Biomes', foreign_keys=[ReplaceWithBiomeType], back_populates='Feature_ValidBiomes_')


t_Feature_ValidTerrains = Table(
    'Feature_ValidTerrains', Base.metadata,
    Column('FeatureType', ForeignKey('Features.FeatureType', ondelete='CASCADE', onupdate='CASCADE'), primary_key=True),
    Column('TerrainType', ForeignKey('Terrains.TerrainType', ondelete='CASCADE', onupdate='CASCADE'), primary_key=True)
)


class GameSystemPrereqs(Base):
    __tablename__ = 'GameSystemPrereqs'

    GameSystemType: Mapped[str] = mapped_column(Text, primary_key=True)
    ConstructibleTypePrereq: Mapped[Optional[str]] = mapped_column(ForeignKey('Constructibles.ConstructibleType', ondelete='CASCADE', onupdate='CASCADE'))
    ProgressionTreeNodePrereq: Mapped[Optional[str]] = mapped_column(ForeignKey('ProgressionTreeNodes.ProgressionTreeNodeType', ondelete='CASCADE', onupdate='CASCADE'))
    ResourceClassPrereq: Mapped[Optional[str]] = mapped_column(ForeignKey('ResourceClasses.ResourceClassType', ondelete='CASCADE', onupdate='CASCADE'))

    Constructibles_: Mapped[Optional['Constructibles']] = relationship('Constructibles', back_populates='GameSystemPrereqs')
    ProgressionTreeNodes_: Mapped[Optional['ProgressionTreeNodes']] = relationship('ProgressionTreeNodes', back_populates='GameSystemPrereqs')
    ResourceClasses_: Mapped[Optional['ResourceClasses']] = relationship('ResourceClasses', back_populates='GameSystemPrereqs')


class Improvements(Base):
    __tablename__ = 'Improvements'

    ConstructibleType: Mapped[str] = mapped_column(ForeignKey('Constructibles.ConstructibleType', ondelete='CASCADE', onupdate='CASCADE'), primary_key=True)
    AdjacentSeaResource: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=text('0'))
    AirSlots: Mapped[int] = mapped_column(Integer, nullable=False, server_default=text('0'))
    BarbarianCamp: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=text('0'))
    BuildInLine: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=text('0'))
    BuildOnFrontier: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=text('0'))
    CanBuildOnNonDistrict: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=text('0'))
    CanBuildOutsideTerritory: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=text('0'))
    CityBuildable: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=text('0'))
    ConstructibleBaseYieldRequired: Mapped[str] = mapped_column(Text, nullable=False, server_default=text('"NO_YIELD"'))
    DefenseModifier: Mapped[int] = mapped_column(Integer, nullable=False, server_default=text('0'))
    DispersalGold: Mapped[int] = mapped_column(Integer, nullable=False, server_default=text('0'))
    Domain: Mapped[str] = mapped_column(Text, nullable=False, server_default=text('"DOMAIN_LAND"'))
    GrantFortification: Mapped[int] = mapped_column(Integer, nullable=False, server_default=text('0'))
    IgnoreNaturalYields: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=text('0'))
    MinimumPopulation: Mapped[int] = mapped_column(Integer, nullable=False, server_default=text('0'))
    MustBeAppealing: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=text('0'))
    OnePerSettlement: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=text('0'))
    RemoveOnEntry: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=text('0'))
    ResourceTier: Mapped[int] = mapped_column(Integer, nullable=False, server_default=text('0'))
    SameAdjacentValid: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=text('1'))
    TownBuildable: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=text('1'))
    UnitBuildable: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=text('0'))
    WeaponSlots: Mapped[int] = mapped_column(Integer, nullable=False, server_default=text('0'))
    Workable: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=text('1'))
    DiscoveryType: Mapped[Optional[str]] = mapped_column(Text)
    Icon: Mapped[Optional[str]] = mapped_column(Text)
    ImprovementOnRemove: Mapped[Optional[str]] = mapped_column(Text)
    TraitType: Mapped[Optional[str]] = mapped_column(ForeignKey('Traits.TraitType', ondelete='SET DEFAULT', onupdate='SET DEFAULT'))

    Traits_: Mapped[Optional['Traits']] = relationship('Traits', back_populates='Improvements')


class IndependentTribeTypes(Base):
    __tablename__ = 'IndependentTribeTypes'

    TribeType: Mapped[str] = mapped_column(Text, primary_key=True)
    AssaultOperation: Mapped[str] = mapped_column(Text, nullable=False, server_default=text('"Independent Assault"'))
    CanBeBefriended: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=text('1'))
    DefenderTagSet: Mapped[str] = mapped_column(ForeignKey('TribeTagSets.TribeTagName', ondelete='CASCADE', onupdate='CASCADE'), nullable=False)
    IgnoreSpacing: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=text('0'))
    NumNormalRaids: Mapped[int] = mapped_column(Integer, nullable=False, server_default=text('1'))
    RaidOperation: Mapped[str] = mapped_column(Text, nullable=False, server_default=text('"Independent Raid"'))
    RespawnTime: Mapped[int] = mapped_column(Integer, nullable=False, server_default=text('-1'))
    UnitBuildTime: Mapped[int] = mapped_column(Integer, nullable=False, server_default=text('8'))
    AdvancedRaidOperation: Mapped[Optional[str]] = mapped_column(Text)
    CampConstructibleType: Mapped[Optional[str]] = mapped_column(ForeignKey('Constructibles.ConstructibleType', ondelete='CASCADE', onupdate='CASCADE'))

    TribeTagSets_: Mapped[list['TribeTagSets']] = relationship('TribeTagSets', secondary='TribeCombatTagSets', back_populates='IndependentTribeTypes')
    TribeTagSets1: Mapped[list['TribeTagSets']] = relationship('TribeTagSets', secondary='TribeCommanderTagSets', back_populates='IndependentTribeTypes_')
    TribeTagSets2: Mapped[list['TribeTagSets']] = relationship('TribeTagSets', secondary='TribeScoutTagSets', back_populates='IndependentTribeTypes1')
    Constructibles_: Mapped[Optional['Constructibles']] = relationship('Constructibles', back_populates='IndependentTribeTypes')
    TribeTagSets3: Mapped['TribeTagSets'] = relationship('TribeTagSets', back_populates='IndependentTribeTypes2')
    Independents: Mapped[list['Independents']] = relationship('Independents', back_populates='IndependentTribeTypes_')


class LegacyModifiers(Base):
    __tablename__ = 'LegacyModifiers'

    LegacyType: Mapped[str] = mapped_column(ForeignKey('Legacies.LegacyType', ondelete='CASCADE', onupdate='CASCADE'), primary_key=True)
    ModifierId: Mapped[str] = mapped_column(Text, nullable=False)
    RequirementSetId: Mapped[str] = mapped_column(ForeignKey('RequirementSets.RequirementSetId', ondelete='CASCADE', onupdate='CASCADE'), nullable=False)

    RequirementSets_: Mapped['RequirementSets'] = relationship('RequirementSets', back_populates='LegacyModifiers')


class LegacyLegacySets(Base):
    __tablename__ = 'Legacy_LegacySets'

    LegacySetType: Mapped[str] = mapped_column(Text, primary_key=True)
    LegacyType: Mapped[str] = mapped_column(ForeignKey('Legacies.LegacyType', ondelete='CASCADE', onupdate='CASCADE'), primary_key=True)

    Legacies_: Mapped['Legacies'] = relationship('Legacies', back_populates='Legacy_LegacySets')


class Projects(Base):
    __tablename__ = 'Projects'

    ProjectType: Mapped[str] = mapped_column(ForeignKey('Types.Type', ondelete='CASCADE', onupdate='CASCADE'), primary_key=True)
    CanPurchase: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=text('0'))
    CityOnly: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=text('0'))
    CostProgressionModel: Mapped[str] = mapped_column(Text, nullable=False, server_default=text('"NO_PROGRESSION_MODEL"'))
    CostProgressionParam1: Mapped[int] = mapped_column(Integer, nullable=False, server_default=text('0'))
    Description: Mapped[str] = mapped_column(Text, nullable=False)
    ExclusiveSpecialization: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=text('0'))
    Food: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=text('0'))
    Name: Mapped[str] = mapped_column(Text, nullable=False)
    OuterDefenseRepair: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=text('0'))
    PrereqAnyCity: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=text('0'))
    PrereqGreatWorks: Mapped[int] = mapped_column(Integer, nullable=False, server_default=text('0'))
    PrereqPopulation: Mapped[int] = mapped_column(Integer, nullable=False, server_default=text('0'))
    PrereqWorkers: Mapped[int] = mapped_column(Integer, nullable=False, server_default=text('0'))
    PrereqWorkersBonusBuilding1Value: Mapped[int] = mapped_column(Integer, nullable=False, server_default=text('0'))
    PrereqWorkersBonusBuilding2Value: Mapped[int] = mapped_column(Integer, nullable=False, server_default=text('0'))
    ProjectVictoryCinematicLocation: Mapped[str] = mapped_column(Text, nullable=False, server_default=text('"NO_PROJECT_VICTORY_CINEMATIC_LOCATION"'))
    RequiresUnlock: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=text('0'))
    ShortName: Mapped[str] = mapped_column(Text, nullable=False)
    SpaceRace: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=text('0'))
    TownDefault: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=text('0'))
    TownOnly: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=text('0'))
    UpgradeToCity: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=text('0'))
    WMD: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=text('0'))
    AdvisorType: Mapped[Optional[str]] = mapped_column(Text)
    Cost: Mapped[Optional[int]] = mapped_column(Integer)
    MaxPlayerInstances: Mapped[Optional[int]] = mapped_column(Integer)
    PopupText: Mapped[Optional[str]] = mapped_column(Text)
    PrereqConstructible: Mapped[Optional[str]] = mapped_column(ForeignKey('Constructibles.ConstructibleType', ondelete='SET DEFAULT', onupdate='SET DEFAULT'))
    PrereqResource: Mapped[Optional[str]] = mapped_column(ForeignKey('Resources.ResourceType', ondelete='SET DEFAULT', onupdate='SET DEFAULT'))
    PrereqWorkersBonusBuilding1: Mapped[Optional[str]] = mapped_column(Text)
    PrereqWorkersBonusBuilding2: Mapped[Optional[str]] = mapped_column(Text)
    RequireCompletedLegacyPathType: Mapped[Optional[str]] = mapped_column(Text)

    Constructibles_: Mapped[Optional['Constructibles']] = relationship('Constructibles', back_populates='Projects')
    Resources_: Mapped[Optional['Resources']] = relationship('Resources', back_populates='Projects')
    ProjectCompletionModifiers: Mapped[list['ProjectCompletionModifiers']] = relationship('ProjectCompletionModifiers', back_populates='Projects_')
    ProjectModifiers: Mapped[list['ProjectModifiers']] = relationship('ProjectModifiers', back_populates='Projects_')
    ProjectPrereqs: Mapped[list['ProjectPrereqs']] = relationship('ProjectPrereqs', foreign_keys='[ProjectPrereqs.PrereqProjectType]', back_populates='Projects_')
    ProjectPrereqs_: Mapped[list['ProjectPrereqs']] = relationship('ProjectPrereqs', foreign_keys='[ProjectPrereqs.ProjectType]', back_populates='Projects1')
    Project_YieldConversions: Mapped[list['ProjectYieldConversions']] = relationship('ProjectYieldConversions', back_populates='Projects_')
    Project_GreatPersonPoints: Mapped[list['ProjectGreatPersonPoints']] = relationship('ProjectGreatPersonPoints', back_populates='Projects_')


class RandomEvents(Base):
    __tablename__ = 'RandomEvents'

    RandomEventType: Mapped[str] = mapped_column(Text, primary_key=True)
    Description: Mapped[str] = mapped_column(Text, nullable=False)
    EffectOperatorType: Mapped[str] = mapped_column(Text, nullable=False)
    EventClass: Mapped[str] = mapped_column(Text, nullable=False)
    Name: Mapped[str] = mapped_column(Text, nullable=False)
    Severity: Mapped[int] = mapped_column(Integer, nullable=False)
    BiomeType: Mapped[Optional[str]] = mapped_column(ForeignKey('Biomes.BiomeType', ondelete='CASCADE', onupdate='CASCADE'))
    Duration: Mapped[Optional[int]] = mapped_column(Integer)
    Hexes: Mapped[Optional[int]] = mapped_column(Integer)
    Movement: Mapped[Optional[int]] = mapped_column(Integer)
    NaturalWonder: Mapped[Optional[str]] = mapped_column(ForeignKey('Features.FeatureType', ondelete='CASCADE', onupdate='CASCADE'))
    Spacing: Mapped[Optional[int]] = mapped_column(Integer)

    Biomes_: Mapped[Optional['Biomes']] = relationship('Biomes', back_populates='RandomEvents')
    Features_: Mapped[Optional['Features']] = relationship('Features', back_populates='RandomEvents')
    RandomEventDamages: Mapped[list['RandomEventDamages']] = relationship('RandomEventDamages', back_populates='RandomEvents_')
    RandomEventFrequencies: Mapped[list['RandomEventFrequencies']] = relationship('RandomEventFrequencies', back_populates='RandomEvents_')
    RandomEventPlotEffects: Mapped[list['RandomEventPlotEffects']] = relationship('RandomEventPlotEffects', back_populates='RandomEvents_')
    RandomEventYields: Mapped[list['RandomEventYields']] = relationship('RandomEventYields', back_populates='RandomEvents_')


class RegionClaimObstacles(Base):
    __tablename__ = 'RegionClaimObstacles'

    ID: Mapped[str] = mapped_column(Text, primary_key=True)
    FeatureClassType: Mapped[Optional[str]] = mapped_column(Text, primary_key=True, nullable=True)
    FeatureType: Mapped[Optional[str]] = mapped_column(ForeignKey('Features.FeatureType', ondelete='CASCADE', onupdate='CASCADE'), primary_key=True, nullable=True)
    RiverType: Mapped[Optional[str]] = mapped_column(Text, primary_key=True, nullable=True)
    TerrainType: Mapped[Optional[str]] = mapped_column(ForeignKey('Terrains.TerrainType', ondelete='CASCADE', onupdate='CASCADE'), primary_key=True, nullable=True)

    Features_: Mapped[Optional['Features']] = relationship('Features', back_populates='RegionClaimObstacles')
    Terrains_: Mapped[Optional['Terrains']] = relationship('Terrains', back_populates='RegionClaimObstacles')


class ResourceHarvests(Base):
    __tablename__ = 'Resource_Harvests'

    ResourceType: Mapped[str] = mapped_column(ForeignKey('Resources.ResourceType', ondelete='CASCADE', onupdate='CASCADE'), primary_key=True)
    YieldType: Mapped[str] = mapped_column(ForeignKey('Yields.YieldType', ondelete='CASCADE', onupdate='CASCADE'), primary_key=True)
    Amount: Mapped[int] = mapped_column(Integer, nullable=False)

    Resources_: Mapped['Resources'] = relationship('Resources', back_populates='Resource_Harvests')
    Yields_: Mapped['Yields'] = relationship('Yields', back_populates='Resource_Harvests')


t_Resource_RequiredCivs = Table(
    'Resource_RequiredCivs', Base.metadata,
    Column('CivilizationType', ForeignKey('Civilizations.CivilizationType', ondelete='CASCADE', onupdate='CASCADE'), primary_key=True),
    Column('ResourceType', ForeignKey('Resources.ResourceType', ondelete='CASCADE', onupdate='CASCADE'), primary_key=True)
)


t_Resource_RequiredLeaders = Table(
    'Resource_RequiredLeaders', Base.metadata,
    Column('LeaderType', ForeignKey('Leaders.LeaderType', ondelete='CASCADE', onupdate='CASCADE'), primary_key=True),
    Column('ResourceType', ForeignKey('Resources.ResourceType', ondelete='CASCADE', onupdate='CASCADE'), primary_key=True)
)


class ResourceValidAges(Base):
    __tablename__ = 'Resource_ValidAges'

    AgeType: Mapped[str] = mapped_column(ForeignKey('Ages.AgeType', ondelete='CASCADE', onupdate='CASCADE'), primary_key=True)
    ResourceType: Mapped[str] = mapped_column(ForeignKey('Resources.ResourceType', ondelete='CASCADE', onupdate='CASCADE'), primary_key=True)
    AIModifierHint: Mapped[Optional[str]] = mapped_column(Text)

    Ages_: Mapped['Ages'] = relationship('Ages', back_populates='Resource_ValidAges')
    Resources_: Mapped['Resources'] = relationship('Resources', back_populates='Resource_ValidAges')


class ResourceValidBiomes(Base):
    __tablename__ = 'Resource_ValidBiomes'

    BiomeType: Mapped[str] = mapped_column(ForeignKey('Biomes.BiomeType', ondelete='CASCADE', onupdate='CASCADE'), primary_key=True)
    ResourceType: Mapped[str] = mapped_column(ForeignKey('Resources.ResourceType', ondelete='CASCADE', onupdate='CASCADE'), primary_key=True)
    TerrainType: Mapped[str] = mapped_column(ForeignKey('Terrains.TerrainType', ondelete='CASCADE', onupdate='CASCADE'), primary_key=True)
    FeatureType: Mapped[Optional[str]] = mapped_column(ForeignKey('Features.FeatureType', ondelete='CASCADE', onupdate='CASCADE'), primary_key=True, nullable=True)

    Biomes_: Mapped['Biomes'] = relationship('Biomes', back_populates='Resource_ValidBiomes')
    Features_: Mapped[Optional['Features']] = relationship('Features', back_populates='Resource_ValidBiomes')
    Resources_: Mapped['Resources'] = relationship('Resources', back_populates='Resource_ValidBiomes')
    Terrains_: Mapped['Terrains'] = relationship('Terrains', back_populates='Resource_ValidBiomes')


class ResourceYieldChanges(Base):
    __tablename__ = 'Resource_YieldChanges'

    ResourceType: Mapped[str] = mapped_column(ForeignKey('Resources.ResourceType', ondelete='CASCADE', onupdate='CASCADE'), primary_key=True)
    YieldType: Mapped[str] = mapped_column(ForeignKey('Yields.YieldType', ondelete='CASCADE', onupdate='CASCADE'), primary_key=True)
    YieldChange: Mapped[int] = mapped_column(Integer, nullable=False)

    Resources_: Mapped['Resources'] = relationship('Resources', back_populates='Resource_YieldChanges')
    Yields_: Mapped['Yields'] = relationship('Yields', back_populates='Resource_YieldChanges')


class Routes(Base):
    __tablename__ = 'Routes'

    RouteType: Mapped[str] = mapped_column(ForeignKey('Types.Type', ondelete='CASCADE', onupdate='CASCADE'), primary_key=True)
    Description: Mapped[str] = mapped_column(Text, nullable=False)
    MovementCost: Mapped[float] = mapped_column(REAL, nullable=False)
    Name: Mapped[str] = mapped_column(Text, nullable=False)
    PlacementRequiresOwnedTile: Mapped[bool] = mapped_column(Boolean, nullable=False)
    PlacementRequiresRoutePresent: Mapped[bool] = mapped_column(Boolean, nullable=False)
    PlacementValue: Mapped[int] = mapped_column(Integer, nullable=False)
    PrereqAge: Mapped[Optional[str]] = mapped_column(ForeignKey('Ages.AgeType', ondelete='SET DEFAULT', onupdate='SET DEFAULT'))
    RequiredConstructible: Mapped[Optional[str]] = mapped_column(ForeignKey('Constructibles.ConstructibleType', ondelete='CASCADE', onupdate='CASCADE'))
    TraitType: Mapped[Optional[str]] = mapped_column(ForeignKey('Traits.TraitType', ondelete='SET DEFAULT', onupdate='SET DEFAULT'))

    Ages_: Mapped[Optional['Ages']] = relationship('Ages', back_populates='Routes')
    Constructibles_: Mapped[Optional['Constructibles']] = relationship('Constructibles', back_populates='Routes')
    Traits_: Mapped[Optional['Traits']] = relationship('Traits', back_populates='Routes')
    Units: Mapped[list['Units']] = relationship('Units', secondary='Route_ValidBuildUnits', back_populates='Routes_')


class StartBiasResources(Base):
    __tablename__ = 'StartBiasResources'

    ResourceType: Mapped[str] = mapped_column(ForeignKey('Resources.ResourceType', ondelete='CASCADE', onupdate='CASCADE'), primary_key=True)
    Score: Mapped[int] = mapped_column(Integer, nullable=False, server_default=text('0'))
    CivilizationType: Mapped[Optional[str]] = mapped_column(ForeignKey('Civilizations.CivilizationType', ondelete='CASCADE', onupdate='CASCADE'), primary_key=True, nullable=True)
    LeaderType: Mapped[Optional[str]] = mapped_column(ForeignKey('Leaders.LeaderType', ondelete='CASCADE', onupdate='CASCADE'), primary_key=True, nullable=True)

    Civilizations_: Mapped[Optional['Civilizations']] = relationship('Civilizations', back_populates='StartBiasResources')
    Leaders_: Mapped[Optional['Leaders']] = relationship('Leaders', back_populates='StartBiasResources')
    Resources_: Mapped['Resources'] = relationship('Resources', back_populates='StartBiasResources')


class TerrainBiomeFeatureYieldChanges(Base):
    __tablename__ = 'TerrainBiomeFeature_YieldChanges'

    BiomeType: Mapped[str] = mapped_column(ForeignKey('Biomes.BiomeType', ondelete='CASCADE', onupdate='CASCADE'), primary_key=True)
    TerrainType: Mapped[str] = mapped_column(ForeignKey('Terrains.TerrainType', ondelete='CASCADE', onupdate='CASCADE'), primary_key=True)
    YieldType: Mapped[str] = mapped_column(ForeignKey('Yields.YieldType', ondelete='CASCADE', onupdate='CASCADE'), primary_key=True)
    ScaleByGameAge: Mapped[int] = mapped_column(Integer, nullable=False, server_default=text('0'))
    YieldChange: Mapped[int] = mapped_column(Integer, nullable=False)
    FeatureType: Mapped[Optional[str]] = mapped_column(ForeignKey('Features.FeatureType', ondelete='CASCADE', onupdate='CASCADE'), primary_key=True, nullable=True)

    Biomes_: Mapped['Biomes'] = relationship('Biomes', back_populates='TerrainBiomeFeature_YieldChanges')
    Features_: Mapped[Optional['Features']] = relationship('Features', back_populates='TerrainBiomeFeature_YieldChanges')
    Terrains_: Mapped['Terrains'] = relationship('Terrains', back_populates='TerrainBiomeFeature_YieldChanges')
    Yields_: Mapped['Yields'] = relationship('Yields', back_populates='TerrainBiomeFeature_YieldChanges')


t_TraditionAttributes = Table(
    'TraditionAttributes', Base.metadata,
    Column('AttributeType', ForeignKey('Attributes.AttributeType', ondelete='CASCADE', onupdate='CASCADE'), primary_key=True),
    Column('TraditionType', ForeignKey('Traditions.TraditionType', ondelete='CASCADE', onupdate='CASCADE'), primary_key=True)
)


t_TraditionModifiers = Table(
    'TraditionModifiers', Base.metadata,
    Column('ModifierId', ForeignKey('Modifiers.ModifierId', ondelete='CASCADE', onupdate='CASCADE'), primary_key=True),
    Column('TraditionType', ForeignKey('Traditions.TraditionType', ondelete='CASCADE', onupdate='CASCADE'), primary_key=True)
)


class UniqueQuarters(Base):
    __tablename__ = 'UniqueQuarters'

    UniqueQuarterType: Mapped[str] = mapped_column(Text, primary_key=True)
    BuildingType1: Mapped[str] = mapped_column(ForeignKey('Constructibles.ConstructibleType', ondelete='CASCADE', onupdate='CASCADE'), nullable=False)
    BuildingType2: Mapped[str] = mapped_column(ForeignKey('Constructibles.ConstructibleType', ondelete='CASCADE', onupdate='CASCADE'), nullable=False)
    Description: Mapped[str] = mapped_column(Text, nullable=False)
    Name: Mapped[str] = mapped_column(Text, nullable=False)
    Tooltip: Mapped[str] = mapped_column(Text, nullable=False)
    TraitType: Mapped[str] = mapped_column(ForeignKey('Traits.TraitType', ondelete='CASCADE', onupdate='CASCADE'), nullable=False)

    Constructibles_: Mapped['Constructibles'] = relationship('Constructibles', foreign_keys=[BuildingType1], back_populates='UniqueQuarters')
    Constructibles1: Mapped['Constructibles'] = relationship('Constructibles', foreign_keys=[BuildingType2], back_populates='UniqueQuarters_')
    Traits_: Mapped['Traits'] = relationship('Traits', back_populates='UniqueQuarters')
    GreatPersonClasses: Mapped[list['GreatPersonClasses']] = relationship('GreatPersonClasses', back_populates='UniqueQuarters_')
    UniqueQuarterModifiers: Mapped[list['UniqueQuarterModifiers']] = relationship('UniqueQuarterModifiers', back_populates='UniqueQuarters_')
    GreatPersonIndividuals: Mapped[list['GreatPersonIndividuals']] = relationship('GreatPersonIndividuals', back_populates='UniqueQuarters_')


class UnitAbilities(Base):
    __tablename__ = 'UnitAbilities'

    UnitAbilityType: Mapped[str] = mapped_column(Text, primary_key=True)
    Inactive: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=text('0'))
    Permanent: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=text('1'))
    ShareWithChildren: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=text('0'))
    ShowFloatTextWhenEarned: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=text('0'))
    AbilityData: Mapped[Optional[str]] = mapped_column(Text)
    AbilityValue: Mapped[Optional[int]] = mapped_column(Integer)
    CommandType: Mapped[Optional[str]] = mapped_column(ForeignKey('UnitCommands.CommandType', ondelete='CASCADE', onupdate='CASCADE'))
    DamageAmount: Mapped[Optional[int]] = mapped_column(Integer)
    Description: Mapped[Optional[str]] = mapped_column(Text)
    KeywordAbilityDuration: Mapped[Optional[int]] = mapped_column(Integer)
    KeywordAbilityType: Mapped[Optional[str]] = mapped_column(ForeignKey('KeywordAbilities.KeywordAbilityType', ondelete='CASCADE', onupdate='CASCADE'))
    KeywordAbilityValue: Mapped[Optional[int]] = mapped_column(Integer)
    Name: Mapped[Optional[str]] = mapped_column(Text)
    OperationType: Mapped[Optional[str]] = mapped_column(ForeignKey('UnitOperations.OperationType', ondelete='CASCADE', onupdate='CASCADE'))

    Modifiers_: Mapped[list['Modifiers']] = relationship('Modifiers', secondary='UnitAbilityModifiers', back_populates='UnitAbilities')
    UnitCommands_: Mapped[Optional['UnitCommands']] = relationship('UnitCommands', back_populates='UnitAbilities')
    KeywordAbilities_: Mapped[Optional['KeywordAbilities']] = relationship('KeywordAbilities', back_populates='UnitAbilities')
    UnitOperations_: Mapped[Optional['UnitOperations']] = relationship('UnitOperations', back_populates='UnitAbilities')
    Units: Mapped[list['Units']] = relationship('Units', secondary='Unit_Abilities', back_populates='UnitAbilities_')
    UnitAbility_TimedAbilities: Mapped[list['UnitAbilityTimedAbilities']] = relationship('UnitAbilityTimedAbilities', foreign_keys='[UnitAbilityTimedAbilities.TimedUnitAbilityType]', back_populates='UnitAbilities_')
    UnitAbility_TimedAbilities_: Mapped[list['UnitAbilityTimedAbilities']] = relationship('UnitAbilityTimedAbilities', foreign_keys='[UnitAbilityTimedAbilities.UnitAbilityType]', back_populates='UnitAbilities1')
    UnitClass_Abilities: Mapped[list['UnitClassAbilities']] = relationship('UnitClassAbilities', back_populates='UnitAbilities_')


class UnitMovementClassObstacles(Base):
    __tablename__ = 'UnitMovementClassObstacles'

    UnitMovementClass: Mapped[str] = mapped_column(Text, primary_key=True)
    EndsTurn: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=text('0'))
    Prohibited: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=text('0'))
    FeatureType: Mapped[Optional[str]] = mapped_column(ForeignKey('Features.FeatureType', ondelete='CASCADE', onupdate='CASCADE'), primary_key=True, nullable=True)
    ObstacleTag: Mapped[Optional[str]] = mapped_column(Text, primary_key=True, nullable=True)
    RiverType: Mapped[Optional[str]] = mapped_column(Text, primary_key=True, nullable=True)
    TerrainType: Mapped[Optional[str]] = mapped_column(ForeignKey('Terrains.TerrainType', ondelete='CASCADE', onupdate='CASCADE'), primary_key=True, nullable=True)

    Features_: Mapped[Optional['Features']] = relationship('Features', back_populates='UnitMovementClassObstacles')
    Terrains_: Mapped[Optional['Terrains']] = relationship('Terrains', back_populates='UnitMovementClassObstacles')


class Units(Base):
    __tablename__ = 'Units'

    UnitType: Mapped[str] = mapped_column(ForeignKey('Types.Type', ondelete='CASCADE', onupdate='CASCADE'), primary_key=True)
    AirSlots: Mapped[int] = mapped_column(Integer, nullable=False, server_default=text('0'))
    AllowBarbarians: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=text('0'))
    AllowEmbarkedDefenseModifiers: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=text('0'))
    AllowTeleportToOtherPlayerCapitals: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=text('0'))
    AntiAirCombat: Mapped[int] = mapped_column(Integer, nullable=False, server_default=text('0'))
    BaseMoves: Mapped[int] = mapped_column(Integer, nullable=False)
    BaseSightRange: Mapped[int] = mapped_column(Integer, nullable=False)
    BuildCharges: Mapped[int] = mapped_column(Integer, nullable=False, server_default=text('0'))
    CanBeDamaged: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=text('1'))
    CanCapture: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=text('1'))
    CanEarnExperience: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=text('0'))
    CanPurchase: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=text('1'))
    CanRetreatWhenCaptured: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=text('0'))
    CanTargetAir: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=text('0'))
    CanTargetLand: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=text('1'))
    CanTrain: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=text('1'))
    CanTriggerDiscovery: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=text('1'))
    CoreClass: Mapped[str] = mapped_column(Text, nullable=False)
    CostProgressionModel: Mapped[str] = mapped_column(Text, nullable=False, server_default=text('"NO_COST_PROGRESSION"'))
    CostProgressionParam1: Mapped[int] = mapped_column(Integer, nullable=False, server_default=text('0'))
    Domain: Mapped[str] = mapped_column(Text, nullable=False)
    EnabledByReligion: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=text('0'))
    EvangelizeBelief: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=text('0'))
    ExtractsArtifacts: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=text('0'))
    FormationClass: Mapped[str] = mapped_column(Text, nullable=False)
    FoundCity: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=text('0'))
    FoundReligion: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=text('0'))
    IgnoreMoves: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=text('0'))
    InitialLevel: Mapped[int] = mapped_column(Integer, nullable=False, server_default=text('1'))
    LaunchInquisition: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=text('0'))
    Maintenance: Mapped[int] = mapped_column(Integer, nullable=False, server_default=text('0'))
    MaintenancePercent: Mapped[int] = mapped_column(Integer, nullable=False, server_default=text('0'))
    MakeTradeRoute: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=text('0'))
    ManualDelete: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=text('1'))
    MustPurchase: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=text('0'))
    Name: Mapped[str] = mapped_column(Text, nullable=False)
    NumRandomChoices: Mapped[int] = mapped_column(Integer, nullable=False, server_default=text('0'))
    Packable: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=text('1'))
    PrereqPopulation: Mapped[int] = mapped_column(Integer, nullable=False, server_default=text('0'))
    ReligionEvictPercent: Mapped[int] = mapped_column(Integer, nullable=False, server_default=text('0'))
    ReligiousHealCharges: Mapped[int] = mapped_column(Integer, nullable=False, server_default=text('0'))
    ReligiousStrength: Mapped[int] = mapped_column(Integer, nullable=False, server_default=text('0'))
    RequiresInquisition: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=text('0'))
    SpreadCharges: Mapped[int] = mapped_column(Integer, nullable=False, server_default=text('0'))
    Spy: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=text('0'))
    Stackable: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=text('0'))
    TeamVisibility: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=text('0'))
    Teleport: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=text('0'))
    TrackReligion: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=text('0'))
    UnitMovementClass: Mapped[str] = mapped_column(Text, nullable=False)
    VictoryUnit: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=text('0'))
    WMDCapable: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=text('0'))
    ZoneOfControl: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=text('0'))
    Description: Mapped[Optional[str]] = mapped_column(Text)
    PromotionClass: Mapped[Optional[str]] = mapped_column(ForeignKey('UnitPromotionClasses.PromotionClassType', ondelete='SET DEFAULT', onupdate='SET DEFAULT'))
    PseudoYieldType: Mapped[Optional[str]] = mapped_column(ForeignKey('PseudoYields.PseudoYieldType', ondelete='SET DEFAULT', onupdate='SET DEFAULT'))
    PurchaseYield: Mapped[Optional[str]] = mapped_column(ForeignKey('Yields.YieldType', ondelete='SET DEFAULT', onupdate='SET DEFAULT'))
    StrategicResource: Mapped[Optional[str]] = mapped_column(ForeignKey('Resources.ResourceType', ondelete='SET DEFAULT', onupdate='SET DEFAULT'))
    Tier: Mapped[Optional[int]] = mapped_column(Integer, server_default=text('0'))
    TraitType: Mapped[Optional[str]] = mapped_column(ForeignKey('Traits.TraitType', ondelete='SET DEFAULT', onupdate='SET DEFAULT'))
    VictoryType: Mapped[Optional[str]] = mapped_column(ForeignKey('Victories.VictoryType', ondelete='CASCADE', onupdate='CASCADE'))

    AdvisoryClasses_: Mapped[list['AdvisoryClasses']] = relationship('AdvisoryClasses', secondary='Unit_Advisories', back_populates='Units')
    UnitAiTypes_: Mapped[list['UnitAiTypes']] = relationship('UnitAiTypes', secondary='UnitAiInfos', back_populates='Units')
    Constructibles_: Mapped[list['Constructibles']] = relationship('Constructibles', secondary='Unit_RequiredConstructibles', back_populates='Units')
    Routes_: Mapped[list['Routes']] = relationship('Routes', secondary='Route_ValidBuildUnits', back_populates='Units')
    UnitAbilities_: Mapped[list['UnitAbilities']] = relationship('UnitAbilities', secondary='Unit_Abilities', back_populates='Units')
    UnitPromotionClasses_: Mapped[Optional['UnitPromotionClasses']] = relationship('UnitPromotionClasses', back_populates='Units')
    PseudoYields_: Mapped[Optional['PseudoYields']] = relationship('PseudoYields', back_populates='Units')
    Yields_: Mapped[Optional['Yields']] = relationship('Yields', back_populates='Units')
    Resources_: Mapped[Optional['Resources']] = relationship('Resources', back_populates='Units')
    Traits_: Mapped[Optional['Traits']] = relationship('Traits', back_populates='Units')
    Victories_: Mapped[Optional['Victories']] = relationship('Victories', back_populates='Units')
    Units: Mapped[list['Units']] = relationship('Units', secondary='CivilopediaUnitsUniqueUpgrades', primaryjoin=lambda: Units.UnitType == t_CivilopediaUnitsUniqueUpgrades.c.BaseUnitType, secondaryjoin=lambda: Units.UnitType == t_CivilopediaUnitsUniqueUpgrades.c.UpgradeUnitType, back_populates='Units_')
    Units_: Mapped[list['Units']] = relationship('Units', secondary='CivilopediaUnitsUniqueUpgrades', primaryjoin=lambda: Units.UnitType == t_CivilopediaUnitsUniqueUpgrades.c.UpgradeUnitType, secondaryjoin=lambda: Units.UnitType == t_CivilopediaUnitsUniqueUpgrades.c.BaseUnitType, back_populates='Units')
    Units1: Mapped[list['Units']] = relationship('Units', secondary='UnitCaptures', primaryjoin=lambda: Units.UnitType == t_UnitCaptures.c.BecomesUnitType, secondaryjoin=lambda: Units.UnitType == t_UnitCaptures.c.CapturedUnitType, back_populates='Units2')
    Units2: Mapped[list['Units']] = relationship('Units', secondary='UnitCaptures', primaryjoin=lambda: Units.UnitType == t_UnitCaptures.c.CapturedUnitType, secondaryjoin=lambda: Units.UnitType == t_UnitCaptures.c.BecomesUnitType, back_populates='Units1')
    Units3: Mapped[list['Units']] = relationship('Units', secondary='UnitReplaces', primaryjoin=lambda: Units.UnitType == t_UnitReplaces.c.CivUniqueUnitType, secondaryjoin=lambda: Units.UnitType == t_UnitReplaces.c.ReplacesUnitType, back_populates='Units4')
    Units4: Mapped[list['Units']] = relationship('Units', secondary='UnitReplaces', primaryjoin=lambda: Units.UnitType == t_UnitReplaces.c.ReplacesUnitType, secondaryjoin=lambda: Units.UnitType == t_UnitReplaces.c.CivUniqueUnitType, back_populates='Units3')
    Units5: Mapped[list['Units']] = relationship('Units', secondary='UnitUpgrades', primaryjoin=lambda: Units.UnitType == t_UnitUpgrades.c.Unit, secondaryjoin=lambda: Units.UnitType == t_UnitUpgrades.c.UpgradeUnit, back_populates='Units6')
    Units6: Mapped[list['Units']] = relationship('Units', secondary='UnitUpgrades', primaryjoin=lambda: Units.UnitType == t_UnitUpgrades.c.UpgradeUnit, secondaryjoin=lambda: Units.UnitType == t_UnitUpgrades.c.Unit, back_populates='Units5')
    AdvancedStartUnits: Mapped[list['AdvancedStartUnits']] = relationship('AdvancedStartUnits', back_populates='Units_')
    AiUnitEfficiencyBonuses: Mapped[list['AiUnitEfficiencyBonuses']] = relationship('AiUnitEfficiencyBonuses', foreign_keys='[AiUnitEfficiencyBonuses.PrimaryUnit]', back_populates='Units_')
    AiUnitEfficiencyBonuses_: Mapped[list['AiUnitEfficiencyBonuses']] = relationship('AiUnitEfficiencyBonuses', foreign_keys='[AiUnitEfficiencyBonuses.SecondaryUnit]', back_populates='Units1')
    BonusMinorStartingUnits: Mapped[list['BonusMinorStartingUnits']] = relationship('BonusMinorStartingUnits', back_populates='Units_')
    Boosts: Mapped[list['Boosts']] = relationship('Boosts', foreign_keys='[Boosts.Unit1Type]', back_populates='Units_')
    Boosts_: Mapped[list['Boosts']] = relationship('Boosts', foreign_keys='[Boosts.Unit2Type]', back_populates='Units1')
    GreatPersonClasses: Mapped[list['GreatPersonClasses']] = relationship('GreatPersonClasses', back_populates='Units_')
    Unit_BuildConstructibles: Mapped[list['UnitBuildConstructibles']] = relationship('UnitBuildConstructibles', back_populates='Units_')
    Unit_Costs: Mapped[list['UnitCosts']] = relationship('UnitCosts', back_populates='Units_')
    Unit_ShadowReplacements: Mapped[list['UnitShadowReplacements']] = relationship('UnitShadowReplacements', back_populates='Units_')
    GreatPersonIndividuals: Mapped[list['GreatPersonIndividuals']] = relationship('GreatPersonIndividuals', foreign_keys='[GreatPersonIndividuals.ActionRequiresOnUnitType]', back_populates='Units_')
    GreatPersonIndividuals_: Mapped[list['GreatPersonIndividuals']] = relationship('GreatPersonIndividuals', foreign_keys='[GreatPersonIndividuals.UnitType]', back_populates='Units1')


class WarehouseYieldChanges(Base):
    __tablename__ = 'Warehouse_YieldChanges'

    ID: Mapped[str] = mapped_column(Text, primary_key=True)
    LakeInCity: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=text('0'))
    MinorRiverInCity: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=text('0'))
    NaturalWonderInCity: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=text('0'))
    NavigableRiverInCity: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=text('0'))
    Overbuilt: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=text('0'))
    ResourceInCity: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=text('0'))
    RouteInCity: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=text('0'))
    YieldChange: Mapped[int] = mapped_column(Integer, nullable=False, server_default=text('0'))
    YieldType: Mapped[str] = mapped_column(ForeignKey('Yields.YieldType', ondelete='CASCADE', onupdate='CASCADE'), nullable=False)
    Age: Mapped[Optional[str]] = mapped_column(Text)
    BiomeInCity: Mapped[Optional[str]] = mapped_column(ForeignKey('Biomes.BiomeType', ondelete='CASCADE', onupdate='CASCADE'))
    ConstructibleInCity: Mapped[Optional[str]] = mapped_column(ForeignKey('Constructibles.ConstructibleType', ondelete='CASCADE', onupdate='CASCADE'))
    DistrictInCity: Mapped[Optional[str]] = mapped_column(ForeignKey('Districts.DistrictType', ondelete='CASCADE', onupdate='CASCADE'))
    FeatureClassInCity: Mapped[Optional[str]] = mapped_column(ForeignKey('FeatureClasses.FeatureClassType', ondelete='CASCADE', onupdate='CASCADE'))
    FeatureInCity: Mapped[Optional[str]] = mapped_column(ForeignKey('Features.FeatureType', ondelete='CASCADE', onupdate='CASCADE'))
    TerrainInCity: Mapped[Optional[str]] = mapped_column(ForeignKey('Terrains.TerrainType', ondelete='CASCADE', onupdate='CASCADE'))
    TerrainTagInCity: Mapped[Optional[str]] = mapped_column(Text)

    Biomes_: Mapped[Optional['Biomes']] = relationship('Biomes', back_populates='Warehouse_YieldChanges')
    Constructibles_: Mapped[Optional['Constructibles']] = relationship('Constructibles', back_populates='Warehouse_YieldChanges')
    Districts_: Mapped[Optional['Districts']] = relationship('Districts', back_populates='Warehouse_YieldChanges')
    FeatureClasses_: Mapped[Optional['FeatureClasses']] = relationship('FeatureClasses', back_populates='Warehouse_YieldChanges')
    Features_: Mapped[Optional['Features']] = relationship('Features', back_populates='Warehouse_YieldChanges')
    Terrains_: Mapped[Optional['Terrains']] = relationship('Terrains', back_populates='Warehouse_YieldChanges')
    Yields_: Mapped['Yields'] = relationship('Yields', back_populates='Warehouse_YieldChanges')
    Constructible_WarehouseYields: Mapped[list['ConstructibleWarehouseYields']] = relationship('ConstructibleWarehouseYields', back_populates='Warehouse_YieldChanges')


class Wonders(Base):
    __tablename__ = 'Wonders'

    ConstructibleType: Mapped[str] = mapped_column(ForeignKey('Constructibles.ConstructibleType', ondelete='CASCADE', onupdate='CASCADE'), primary_key=True)
    AdjacentCapital: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=text('0'))
    AdjacentToLand: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=text('0'))
    AdjacentToMountain: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=text('0'))
    BuildOnFrontier: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=text('0'))
    MaxPerPlayer: Mapped[int] = mapped_column(Integer, nullable=False, server_default=text('1'))
    MaxWorldInstances: Mapped[int] = mapped_column(Integer, nullable=False, server_default=text('-1'))
    MustBeLake: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=text('0'))
    MustNotBeLake: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=text('0'))
    RequiredConstructibleInSettlementCount: Mapped[int] = mapped_column(Integer, nullable=False, server_default=text('1'))
    AdjacentConstructible: Mapped[Optional[str]] = mapped_column(ForeignKey('Constructibles.ConstructibleType', ondelete='CASCADE', onupdate='CASCADE'))
    AdjacentResource: Mapped[Optional[str]] = mapped_column(ForeignKey('Resources.ResourceType', ondelete='SET DEFAULT', onupdate='SET DEFAULT'))
    RequiredConstructibleInSettlement: Mapped[Optional[str]] = mapped_column(ForeignKey('Constructibles.ConstructibleType', ondelete='CASCADE', onupdate='CASCADE'))

    Constructibles_: Mapped[Optional['Constructibles']] = relationship('Constructibles', foreign_keys=[AdjacentConstructible], back_populates='Wonders')
    Resources_: Mapped[Optional['Resources']] = relationship('Resources', back_populates='Wonders')
    Constructibles1: Mapped[Optional['Constructibles']] = relationship('Constructibles', foreign_keys=[RequiredConstructibleInSettlement], back_populates='Wonders_')


class AIUnitPrioritizedActions(Base):
    __tablename__ = 'AIUnitPrioritizedActions'

    UnitType: Mapped[str] = mapped_column(ForeignKey('Units.UnitType', ondelete='CASCADE', onupdate='CASCADE'), primary_key=True)
    ChargedUnitAbilityType: Mapped[Optional[str]] = mapped_column(ForeignKey('ChargedUnitAbilities.UnitAbilityType', ondelete='CASCADE', onupdate='CASCADE'))
    CommandType: Mapped[Optional[str]] = mapped_column(ForeignKey('UnitCommands.CommandType', ondelete='CASCADE', onupdate='CASCADE'))
    OperationType: Mapped[Optional[str]] = mapped_column(ForeignKey('UnitOperations.OperationType', ondelete='CASCADE', onupdate='CASCADE'))

    ChargedUnitAbilities_: Mapped[Optional['ChargedUnitAbilities']] = relationship('ChargedUnitAbilities', back_populates='AIUnitPrioritizedActions')
    UnitCommands_: Mapped[Optional['UnitCommands']] = relationship('UnitCommands', back_populates='AIUnitPrioritizedActions')
    UnitOperations_: Mapped[Optional['UnitOperations']] = relationship('UnitOperations', back_populates='AIUnitPrioritizedActions')


class AdvancedStartUnits(Base):
    __tablename__ = 'AdvancedStartUnits'

    Age: Mapped[str] = mapped_column(ForeignKey('Ages.AgeType', ondelete='CASCADE', onupdate='CASCADE'), primary_key=True)
    District: Mapped[str] = mapped_column(ForeignKey('Districts.DistrictType', ondelete='CASCADE', onupdate='CASCADE'), primary_key=True, server_default=text('"DISTRICT_CITY_CENTER"'))
    Unit: Mapped[str] = mapped_column(ForeignKey('Units.UnitType', ondelete='CASCADE', onupdate='CASCADE'), primary_key=True)
    AiOnly: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=text('0'))
    AltStartOnly: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=text('0'))
    Capital: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=text('0'))
    City: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=text('0'))
    DifficultyDelta: Mapped[float] = mapped_column(REAL, nullable=False, server_default=text('0'))
    NotStartTile: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=text('0'))
    Quantity: Mapped[int] = mapped_column(Integer, nullable=False, server_default=text('1'))
    MinDifficulty: Mapped[Optional[str]] = mapped_column(ForeignKey('Difficulties.DifficultyType', ondelete='CASCADE', onupdate='CASCADE'), primary_key=True, nullable=True)

    Ages_: Mapped['Ages'] = relationship('Ages', back_populates='AdvancedStartUnits')
    Districts_: Mapped['Districts'] = relationship('Districts', back_populates='AdvancedStartUnits')
    Difficulties_: Mapped[Optional['Difficulties']] = relationship('Difficulties', back_populates='AdvancedStartUnits')
    Units_: Mapped['Units'] = relationship('Units', back_populates='AdvancedStartUnits')


class AiUnitEfficiencyBonuses(Base):
    __tablename__ = 'AiUnitEfficiencyBonuses'

    PrimaryUnit: Mapped[str] = mapped_column(ForeignKey('Units.UnitType', ondelete='CASCADE', onupdate='CASCADE'), primary_key=True)
    SecondaryUnit: Mapped[str] = mapped_column(ForeignKey('Units.UnitType', ondelete='CASCADE', onupdate='CASCADE'), primary_key=True)
    EfficiencyBonus: Mapped[float] = mapped_column(REAL, nullable=False)

    Units_: Mapped['Units'] = relationship('Units', foreign_keys=[PrimaryUnit], back_populates='AiUnitEfficiencyBonuses')
    Units1: Mapped['Units'] = relationship('Units', foreign_keys=[SecondaryUnit], back_populates='AiUnitEfficiencyBonuses_')


class BarbarianTribeNames(Base):
    __tablename__ = 'BarbarianTribeNames'

    TribeNameType: Mapped[str] = mapped_column(Text, primary_key=True)
    TribeDisplayName: Mapped[str] = mapped_column(Text, nullable=False)
    TribeType: Mapped[str] = mapped_column(ForeignKey('BarbarianTribes.TribeType', ondelete='CASCADE', onupdate='CASCADE'), nullable=False)
    NumMilitary: Mapped[Optional[int]] = mapped_column(Integer, server_default=text('5'))
    NumScouts: Mapped[Optional[int]] = mapped_column(Integer)
    PercentRangedUnits: Mapped[Optional[int]] = mapped_column(Integer)
    RaidingBehaviorTree: Mapped[Optional[str]] = mapped_column(Text)
    RaidingBoldness: Mapped[Optional[int]] = mapped_column(Integer)
    ScoutingBehaviorTree: Mapped[Optional[str]] = mapped_column(Text)
    TurnsToWarriorSpawn: Mapped[Optional[int]] = mapped_column(Integer)

    BarbarianTribes_: Mapped['BarbarianTribes'] = relationship('BarbarianTribes', back_populates='BarbarianTribeNames')
    BarbarianTribeForces: Mapped[list['BarbarianTribeForces']] = relationship('BarbarianTribeForces', back_populates='BarbarianTribeNames_')


class BonusMinorStartingUnits(Base):
    __tablename__ = 'BonusMinorStartingUnits'

    Age: Mapped[str] = mapped_column(ForeignKey('Ages.AgeType', ondelete='CASCADE', onupdate='CASCADE'), primary_key=True)
    Unit: Mapped[str] = mapped_column(ForeignKey('Units.UnitType', ondelete='CASCADE', onupdate='CASCADE'), primary_key=True)
    DifficultyDelta: Mapped[float] = mapped_column(REAL, nullable=False, server_default=text('0'))
    District: Mapped[str] = mapped_column(Text, nullable=False, server_default=text('"DISTRICT_CITY_CENTER"'))
    OnDistrictCreated: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=text('0'))
    Quantity: Mapped[int] = mapped_column(Integer, nullable=False, server_default=text('1'))
    MinDifficulty: Mapped[Optional[str]] = mapped_column(ForeignKey('Difficulties.DifficultyType', ondelete='CASCADE', onupdate='CASCADE'), primary_key=True, nullable=True)

    Ages_: Mapped['Ages'] = relationship('Ages', back_populates='BonusMinorStartingUnits')
    Difficulties_: Mapped[Optional['Difficulties']] = relationship('Difficulties', back_populates='BonusMinorStartingUnits')
    Units_: Mapped['Units'] = relationship('Units', back_populates='BonusMinorStartingUnits')


class Boosts(Base):
    __tablename__ = 'Boosts'

    BoostID: Mapped[int] = mapped_column(Integer, primary_key=True)
    Boost: Mapped[int] = mapped_column(Integer, nullable=False)
    BoostClass: Mapped[str] = mapped_column(ForeignKey('BoostNames.BoostType', ondelete='CASCADE', onupdate='CASCADE'), nullable=False)
    NumItems: Mapped[int] = mapped_column(Integer, nullable=False, server_default=text('0'))
    RequiresResource: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=text('0'))
    TriggerDescription: Mapped[str] = mapped_column(Text, nullable=False)
    TriggerId: Mapped[int] = mapped_column(Integer, nullable=False, server_default=text('0'))
    TriggerLongDescription: Mapped[str] = mapped_column(Text, nullable=False)
    ConstructibleType: Mapped[Optional[str]] = mapped_column(ForeignKey('Constructibles.ConstructibleType', ondelete='CASCADE', onupdate='CASCADE'))
    DistrictType: Mapped[Optional[str]] = mapped_column(ForeignKey('Districts.DistrictType', ondelete='CASCADE', onupdate='CASCADE'))
    RequirementSetId: Mapped[Optional[str]] = mapped_column(Text)
    ResourceType: Mapped[Optional[str]] = mapped_column(ForeignKey('Resources.ResourceType', ondelete='CASCADE', onupdate='CASCADE'))
    Unit1Type: Mapped[Optional[str]] = mapped_column(ForeignKey('Units.UnitType', ondelete='CASCADE', onupdate='CASCADE'))
    Unit2Type: Mapped[Optional[str]] = mapped_column(ForeignKey('Units.UnitType', ondelete='CASCADE', onupdate='CASCADE'))

    BoostNames_: Mapped['BoostNames'] = relationship('BoostNames', back_populates='Boosts')
    Constructibles_: Mapped[Optional['Constructibles']] = relationship('Constructibles', back_populates='Boosts')
    Districts_: Mapped[Optional['Districts']] = relationship('Districts', back_populates='Boosts')
    Resources_: Mapped[Optional['Resources']] = relationship('Resources', back_populates='Boosts')
    Units_: Mapped[Optional['Units']] = relationship('Units', foreign_keys=[Unit1Type], back_populates='Boosts')
    Units1: Mapped[Optional['Units']] = relationship('Units', foreign_keys=[Unit2Type], back_populates='Boosts_')


t_CivilopediaUnitsUniqueUpgrades = Table(
    'CivilopediaUnitsUniqueUpgrades', Base.metadata,
    Column('BaseUnitType', ForeignKey('Units.UnitType', ondelete='CASCADE', onupdate='CASCADE'), primary_key=True),
    Column('UpgradeUnitType', ForeignKey('Units.UnitType', ondelete='CASCADE', onupdate='CASCADE'), primary_key=True)
)


class ConstructibleAdjacencies(Base):
    __tablename__ = 'Constructible_Adjacencies'

    ConstructibleType: Mapped[str] = mapped_column(ForeignKey('Constructibles.ConstructibleType', ondelete='CASCADE', onupdate='CASCADE'), primary_key=True)
    YieldChangeId: Mapped[str] = mapped_column(ForeignKey('Adjacency_YieldChanges.ID', ondelete='CASCADE', onupdate='CASCADE'), primary_key=True)
    Name: Mapped[str] = mapped_column(Text, nullable=False, server_default=text('""'))
    RequiresActivation: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=text('0'))

    Constructibles_: Mapped['Constructibles'] = relationship('Constructibles', back_populates='Constructible_Adjacencies')
    Adjacency_YieldChanges: Mapped['AdjacencyYieldChanges'] = relationship('AdjacencyYieldChanges', back_populates='Constructible_Adjacencies')


class ConstructibleWarehouseYields(Base):
    __tablename__ = 'Constructible_WarehouseYields'

    ConstructibleType: Mapped[str] = mapped_column(ForeignKey('Constructibles.ConstructibleType', ondelete='CASCADE', onupdate='CASCADE'), primary_key=True)
    YieldChangeId: Mapped[str] = mapped_column(ForeignKey('Warehouse_YieldChanges.ID', ondelete='CASCADE', onupdate='CASCADE'), primary_key=True)
    RequiresActivation: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=text('0'))

    Constructibles_: Mapped['Constructibles'] = relationship('Constructibles', back_populates='Constructible_WarehouseYields')
    Warehouse_YieldChanges: Mapped['WarehouseYieldChanges'] = relationship('WarehouseYieldChanges', back_populates='Constructible_WarehouseYields')


class ConstructibleWildcardAdjacencies(Base):
    __tablename__ = 'Constructible_WildcardAdjacencies'

    YieldChangeId: Mapped[str] = mapped_column(ForeignKey('Adjacency_YieldChanges.ID', ondelete='CASCADE', onupdate='CASCADE'), primary_key=True)
    RequiresActivation: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=text('0'))
    ConstructibleClass: Mapped[Optional[str]] = mapped_column(Text)
    ConstructibleTag: Mapped[Optional[str]] = mapped_column(Text)
    CurrentAgeConstructiblesOnly: Mapped[Optional[bool]] = mapped_column(Boolean, server_default=text('0'))
    HasBiome: Mapped[Optional[str]] = mapped_column(Text)
    HasNavigableRiver: Mapped[Optional[bool]] = mapped_column(Boolean)
    HasTerrain: Mapped[Optional[str]] = mapped_column(Text)
    HasYield: Mapped[Optional[str]] = mapped_column(Text)


class ConstructibleWildcardWarehouseYields(Base):
    __tablename__ = 'Constructible_WildcardWarehouseYields'

    YieldChangeId: Mapped[str] = mapped_column(ForeignKey('Warehouse_YieldChanges.ID', ondelete='CASCADE', onupdate='CASCADE'), primary_key=True)
    RequiresActivation: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=text('0'))
    ConstructibleTag: Mapped[Optional[str]] = mapped_column(Text)


t_ExcludedAdjacencies = Table(
    'ExcludedAdjacencies', Base.metadata,
    Column('TraitType', ForeignKey('Traits.TraitType', ondelete='CASCADE', onupdate='CASCADE'), primary_key=True),
    Column('YieldChangeId', ForeignKey('Adjacency_YieldChanges.ID', ondelete='CASCADE', onupdate='CASCADE'), primary_key=True)
)


class GreatPersonClasses(Base):
    __tablename__ = 'GreatPersonClasses'

    GreatPersonClassType: Mapped[str] = mapped_column(ForeignKey('Types.Type', ondelete='CASCADE', onupdate='CASCADE'), primary_key=True)
    ActionIcon: Mapped[str] = mapped_column(Text, nullable=False)
    AvailableInTimeline: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=text('1'))
    CityStatesSuzerained: Mapped[int] = mapped_column(Integer, nullable=False, server_default=text('0'))
    GenerateDuplicateIndividuals: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=text('0'))
    IconString: Mapped[str] = mapped_column(Text, nullable=False)
    Name: Mapped[str] = mapped_column(Text, nullable=False)
    PopulationRequired: Mapped[int] = mapped_column(Integer, nullable=False, server_default=text('0'))
    UnitType: Mapped[str] = mapped_column(ForeignKey('Units.UnitType', ondelete='CASCADE', onupdate='CASCADE'), nullable=False)
    ConstructibleType: Mapped[Optional[str]] = mapped_column(ForeignKey('Constructibles.ConstructibleType', ondelete='CASCADE', onupdate='CASCADE'))
    MaxPlayerInstances: Mapped[Optional[int]] = mapped_column(Integer)
    PseudoYieldType: Mapped[Optional[str]] = mapped_column(ForeignKey('PseudoYields.PseudoYieldType', ondelete='CASCADE', onupdate='CASCADE'))
    UniqueQuarterType: Mapped[Optional[str]] = mapped_column(ForeignKey('UniqueQuarters.UniqueQuarterType', ondelete='CASCADE', onupdate='CASCADE'))

    Constructibles_: Mapped[Optional['Constructibles']] = relationship('Constructibles', back_populates='GreatPersonClasses')
    PseudoYields_: Mapped[Optional['PseudoYields']] = relationship('PseudoYields', back_populates='GreatPersonClasses')
    UniqueQuarters_: Mapped[Optional['UniqueQuarters']] = relationship('UniqueQuarters', back_populates='GreatPersonClasses')
    Units_: Mapped['Units'] = relationship('Units', back_populates='GreatPersonClasses')
    Traits_: Mapped[list['Traits']] = relationship('Traits', secondary='ExcludedGreatPersonClasses', back_populates='GreatPersonClasses')
    Constructible_GreatPersonPoints: Mapped[list['ConstructibleGreatPersonPoints']] = relationship('ConstructibleGreatPersonPoints', back_populates='GreatPersonClasses_')
    GreatPersonIndividuals: Mapped[list['GreatPersonIndividuals']] = relationship('GreatPersonIndividuals', back_populates='GreatPersonClasses_')
    Map_GreatPersonClasses: Mapped[list['MapGreatPersonClasses']] = relationship('MapGreatPersonClasses', back_populates='GreatPersonClasses_')
    Project_GreatPersonPoints: Mapped[list['ProjectGreatPersonPoints']] = relationship('ProjectGreatPersonPoints', back_populates='GreatPersonClasses_')


class Independents(Base):
    __tablename__ = 'Independents'

    IndependentType: Mapped[str] = mapped_column(Text, primary_key=True)
    Affinity: Mapped[str] = mapped_column(ForeignKey('Affinities.Affinity', ondelete='CASCADE', onupdate='CASCADE'), nullable=False)
    CityStateIsCity: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=text('0'))
    CityStateName: Mapped[str] = mapped_column(Text, nullable=False)
    CityStateType: Mapped[str] = mapped_column(ForeignKey('CityStateTypes.CityStateType', ondelete='CASCADE', onupdate='CASCADE'), nullable=False)
    Name: Mapped[str] = mapped_column(Text, nullable=False)
    TribeType: Mapped[str] = mapped_column(ForeignKey('IndependentTribeTypes.TribeType', ondelete='CASCADE', onupdate='CASCADE'), nullable=False, server_default=text('"TRIBE_DEFAULT"'))
    BiomeType: Mapped[Optional[str]] = mapped_column(ForeignKey('Biomes.BiomeType', ondelete='CASCADE', onupdate='CASCADE'))

    Affinities_: Mapped['Affinities'] = relationship('Affinities', back_populates='Independents')
    Biomes_: Mapped[Optional['Biomes']] = relationship('Biomes', back_populates='Independents')
    CityStateTypes_: Mapped['CityStateTypes'] = relationship('CityStateTypes', back_populates='Independents')
    IndependentTribeTypes_: Mapped['IndependentTribeTypes'] = relationship('IndependentTribeTypes', back_populates='Independents')
    VisArt_IndependentBuildingCultures: Mapped[list['VisArtIndependentBuildingCultures']] = relationship('VisArtIndependentBuildingCultures', back_populates='Independents_')
    VisArt_IndependentUnitCultures: Mapped[list['VisArtIndependentUnitCultures']] = relationship('VisArtIndependentUnitCultures', back_populates='Independents_')


class ProjectCompletionModifiers(Base):
    __tablename__ = 'ProjectCompletionModifiers'

    ModifierId: Mapped[str] = mapped_column(Text, primary_key=True)
    ProjectType: Mapped[str] = mapped_column(ForeignKey('Projects.ProjectType', ondelete='CASCADE', onupdate='CASCADE'), primary_key=True)

    Projects_: Mapped['Projects'] = relationship('Projects', back_populates='ProjectCompletionModifiers')


class ProjectModifiers(Base):
    __tablename__ = 'ProjectModifiers'

    ModifierId: Mapped[str] = mapped_column(Text, primary_key=True)
    ProjectType: Mapped[str] = mapped_column(ForeignKey('Projects.ProjectType', ondelete='CASCADE', onupdate='CASCADE'), primary_key=True)

    Projects_: Mapped['Projects'] = relationship('Projects', back_populates='ProjectModifiers')


class ProjectPrereqs(Base):
    __tablename__ = 'ProjectPrereqs'

    PrereqProjectType: Mapped[str] = mapped_column(ForeignKey('Projects.ProjectType', ondelete='CASCADE', onupdate='CASCADE'), primary_key=True)
    ProjectType: Mapped[str] = mapped_column(ForeignKey('Projects.ProjectType', ondelete='CASCADE', onupdate='CASCADE'), primary_key=True)
    MinimumPlayerInstances: Mapped[int] = mapped_column(Integer, nullable=False)

    Projects_: Mapped['Projects'] = relationship('Projects', foreign_keys=[PrereqProjectType], back_populates='ProjectPrereqs')
    Projects1: Mapped['Projects'] = relationship('Projects', foreign_keys=[ProjectType], back_populates='ProjectPrereqs_')


class ProjectYieldConversions(Base):
    __tablename__ = 'Project_YieldConversions'

    ProjectType: Mapped[str] = mapped_column(ForeignKey('Projects.ProjectType', ondelete='CASCADE', onupdate='CASCADE'), primary_key=True)
    YieldType: Mapped[str] = mapped_column(ForeignKey('Yields.YieldType', ondelete='CASCADE', onupdate='CASCADE'), primary_key=True)
    PercentOfProductionRate: Mapped[int] = mapped_column(Integer, nullable=False, server_default=text('0'))

    Projects_: Mapped['Projects'] = relationship('Projects', back_populates='Project_YieldConversions')
    Yields_: Mapped['Yields'] = relationship('Yields', back_populates='Project_YieldConversions')


class RandomEventDamages(Base):
    __tablename__ = 'RandomEventDamages'

    DamageType: Mapped[str] = mapped_column(Text, primary_key=True)
    RandomEventType: Mapped[str] = mapped_column(ForeignKey('RandomEvents.RandomEventType', ondelete='CASCADE', onupdate='CASCADE'), primary_key=True)
    Percentage: Mapped[int] = mapped_column(Integer, nullable=False)
    MaxHP: Mapped[Optional[int]] = mapped_column(Integer)
    MinHP: Mapped[Optional[int]] = mapped_column(Integer)

    RandomEvents_: Mapped['RandomEvents'] = relationship('RandomEvents', back_populates='RandomEventDamages')


class RandomEventFrequencies(Base):
    __tablename__ = 'RandomEventFrequencies'

    RandomEventType: Mapped[str] = mapped_column(ForeignKey('RandomEvents.RandomEventType', ondelete='CASCADE', onupdate='CASCADE'), primary_key=True)
    RealismSettingType: Mapped[str] = mapped_column(ForeignKey('RealismSettings.RealismSettingType', ondelete='CASCADE', onupdate='CASCADE'), primary_key=True)
    OccurrencesPerAge: Mapped[float] = mapped_column(REAL, nullable=False)

    RandomEvents_: Mapped['RandomEvents'] = relationship('RandomEvents', back_populates='RandomEventFrequencies')
    RealismSettings_: Mapped['RealismSettings'] = relationship('RealismSettings', back_populates='RandomEventFrequencies')


class RandomEventPlotEffects(Base):
    __tablename__ = 'RandomEventPlotEffects'

    PlotEffectType: Mapped[str] = mapped_column(Text, primary_key=True)
    RandomEventType: Mapped[str] = mapped_column(ForeignKey('RandomEvents.RandomEventType', ondelete='CASCADE', onupdate='CASCADE'), primary_key=True)
    Duration: Mapped[int] = mapped_column(Integer, nullable=False)

    RandomEvents_: Mapped['RandomEvents'] = relationship('RandomEvents', back_populates='RandomEventPlotEffects')


class RandomEventYields(Base):
    __tablename__ = 'RandomEventYields'

    RandomEventType: Mapped[str] = mapped_column(ForeignKey('RandomEvents.RandomEventType', ondelete='CASCADE', onupdate='CASCADE'), primary_key=True)
    YieldType: Mapped[str] = mapped_column(ForeignKey('Yields.YieldType', ondelete='CASCADE', onupdate='CASCADE'), primary_key=True)
    Percentage: Mapped[int] = mapped_column(Integer, nullable=False)

    RandomEvents_: Mapped['RandomEvents'] = relationship('RandomEvents', back_populates='RandomEventYields')
    Yields_: Mapped['Yields'] = relationship('Yields', back_populates='RandomEventYields')


t_Route_ValidBuildUnits = Table(
    'Route_ValidBuildUnits', Base.metadata,
    Column('RouteType', ForeignKey('Routes.RouteType', ondelete='CASCADE', onupdate='CASCADE'), primary_key=True),
    Column('UnitType', ForeignKey('Units.UnitType', ondelete='CASCADE', onupdate='CASCADE'), primary_key=True)
)


t_TribeCombatTagSets = Table(
    'TribeCombatTagSets', Base.metadata,
    Column('TribeTagSetName', ForeignKey('TribeTagSets.TribeTagName', ondelete='CASCADE', onupdate='CASCADE'), primary_key=True),
    Column('TribeTypeName', ForeignKey('IndependentTribeTypes.TribeType', ondelete='CASCADE', onupdate='CASCADE'), primary_key=True)
)


t_TribeCommanderTagSets = Table(
    'TribeCommanderTagSets', Base.metadata,
    Column('TribeTagSetName', ForeignKey('TribeTagSets.TribeTagName', ondelete='CASCADE', onupdate='CASCADE'), primary_key=True),
    Column('TribeTypeName', ForeignKey('IndependentTribeTypes.TribeType', ondelete='CASCADE', onupdate='CASCADE'), primary_key=True)
)


t_TribeScoutTagSets = Table(
    'TribeScoutTagSets', Base.metadata,
    Column('TribeTagSetName', ForeignKey('TribeTagSets.TribeTagName', ondelete='CASCADE', onupdate='CASCADE'), primary_key=True),
    Column('TribeTypeName', ForeignKey('IndependentTribeTypes.TribeType', ondelete='CASCADE', onupdate='CASCADE'), primary_key=True)
)


class UniqueQuarterModifiers(Base):
    __tablename__ = 'UniqueQuarterModifiers'

    ModifierID: Mapped[str] = mapped_column(Text, primary_key=True)
    UniqueQuarterType: Mapped[str] = mapped_column(ForeignKey('UniqueQuarters.UniqueQuarterType', ondelete='CASCADE', onupdate='CASCADE'), primary_key=True)

    UniqueQuarters_: Mapped['UniqueQuarters'] = relationship('UniqueQuarters', back_populates='UniqueQuarterModifiers')


t_UnitAbilityModifiers = Table(
    'UnitAbilityModifiers', Base.metadata,
    Column('ModifierId', ForeignKey('Modifiers.ModifierId', ondelete='CASCADE', onupdate='CASCADE'), primary_key=True),
    Column('UnitAbilityType', ForeignKey('UnitAbilities.UnitAbilityType', ondelete='CASCADE', onupdate='CASCADE'), primary_key=True)
)


class UnitAbilityTimedAbilities(Base):
    __tablename__ = 'UnitAbility_TimedAbilities'

    TimedUnitAbilityType: Mapped[str] = mapped_column(ForeignKey('UnitAbilities.UnitAbilityType', ondelete='CASCADE', onupdate='CASCADE'), primary_key=True)
    UnitAbilityType: Mapped[str] = mapped_column(ForeignKey('UnitAbilities.UnitAbilityType', ondelete='CASCADE', onupdate='CASCADE'), primary_key=True)
    Duration: Mapped[int] = mapped_column(Integer, nullable=False)

    UnitAbilities_: Mapped['UnitAbilities'] = relationship('UnitAbilities', foreign_keys=[TimedUnitAbilityType], back_populates='UnitAbility_TimedAbilities')
    UnitAbilities1: Mapped['UnitAbilities'] = relationship('UnitAbilities', foreign_keys=[UnitAbilityType], back_populates='UnitAbility_TimedAbilities_')


t_UnitAiInfos = Table(
    'UnitAiInfos', Base.metadata,
    Column('AiType', ForeignKey('UnitAiTypes.AiType', ondelete='CASCADE', onupdate='CASCADE'), primary_key=True),
    Column('UnitType', ForeignKey('Units.UnitType', ondelete='CASCADE', onupdate='CASCADE'), primary_key=True)
)


t_UnitCaptures = Table(
    'UnitCaptures', Base.metadata,
    Column('BecomesUnitType', ForeignKey('Units.UnitType', ondelete='CASCADE', onupdate='CASCADE'), primary_key=True),
    Column('CapturedUnitType', ForeignKey('Units.UnitType', ondelete='CASCADE', onupdate='CASCADE'), primary_key=True)
)


class UnitClassAbilities(Base):
    __tablename__ = 'UnitClass_Abilities'

    UnitAbilityType: Mapped[str] = mapped_column(ForeignKey('UnitAbilities.UnitAbilityType', ondelete='CASCADE', onupdate='CASCADE'), primary_key=True)
    UnitClassType: Mapped[str] = mapped_column(Text, primary_key=True)

    UnitAbilities_: Mapped['UnitAbilities'] = relationship('UnitAbilities', back_populates='UnitClass_Abilities')


t_UnitReplaces = Table(
    'UnitReplaces', Base.metadata,
    Column('CivUniqueUnitType', ForeignKey('Units.UnitType', ondelete='CASCADE', onupdate='CASCADE'), primary_key=True),
    Column('ReplacesUnitType', ForeignKey('Units.UnitType', ondelete='CASCADE', onupdate='CASCADE'), nullable=False)
)


t_UnitUpgrades = Table(
    'UnitUpgrades', Base.metadata,
    Column('Unit', ForeignKey('Units.UnitType', ondelete='CASCADE', onupdate='CASCADE'), primary_key=True),
    Column('UpgradeUnit', ForeignKey('Units.UnitType', ondelete='CASCADE', onupdate='CASCADE'), nullable=False)
)


t_Unit_Abilities = Table(
    'Unit_Abilities', Base.metadata,
    Column('UnitAbilityType', ForeignKey('UnitAbilities.UnitAbilityType', ondelete='CASCADE', onupdate='CASCADE'), primary_key=True),
    Column('UnitType', ForeignKey('Units.UnitType', ondelete='CASCADE', onupdate='CASCADE'), primary_key=True)
)


t_Unit_Advisories = Table(
    'Unit_Advisories', Base.metadata,
    Column('AdvisoryClassType', ForeignKey('AdvisoryClasses.AdvisoryClassType', ondelete='CASCADE', onupdate='CASCADE'), primary_key=True),
    Column('UnitType', ForeignKey('Units.UnitType', ondelete='CASCADE', onupdate='CASCADE'), primary_key=True)
)


class UnitBuildConstructibles(Base):
    __tablename__ = 'Unit_BuildConstructibles'

    ConstructibleType: Mapped[str] = mapped_column(ForeignKey('Constructibles.ConstructibleType', ondelete='CASCADE', onupdate='CASCADE'), primary_key=True)
    UnitType: Mapped[str] = mapped_column(ForeignKey('Units.UnitType', ondelete='CASCADE', onupdate='CASCADE'), primary_key=True)
    CanZone: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=text('0'))

    Constructibles_: Mapped['Constructibles'] = relationship('Constructibles', back_populates='Unit_BuildConstructibles')
    Units_: Mapped['Units'] = relationship('Units', back_populates='Unit_BuildConstructibles')


class UnitCosts(Base):
    __tablename__ = 'Unit_Costs'

    UnitType: Mapped[str] = mapped_column(ForeignKey('Units.UnitType', ondelete='CASCADE', onupdate='CASCADE'), primary_key=True)
    YieldType: Mapped[str] = mapped_column(ForeignKey('Yields.YieldType', ondelete='CASCADE', onupdate='CASCADE'), primary_key=True)
    Cost: Mapped[int] = mapped_column(Integer, nullable=False)

    Units_: Mapped['Units'] = relationship('Units', back_populates='Unit_Costs')
    Yields_: Mapped['Yields'] = relationship('Yields', back_populates='Unit_Costs')


t_Unit_RequiredConstructibles = Table(
    'Unit_RequiredConstructibles', Base.metadata,
    Column('ConstructibleType', ForeignKey('Constructibles.ConstructibleType', ondelete='CASCADE', onupdate='CASCADE'), primary_key=True),
    Column('UnitType', ForeignKey('Units.UnitType', ondelete='CASCADE', onupdate='CASCADE'), primary_key=True)
)


class UnitShadowReplacements(Base):
    __tablename__ = 'Unit_ShadowReplacements'

    Tag: Mapped[str] = mapped_column(Text, primary_key=True)
    UnitType: Mapped[str] = mapped_column(ForeignKey('Units.UnitType', ondelete='CASCADE', onupdate='CASCADE'), primary_key=True)
    CoreClass: Mapped[str] = mapped_column(Text, nullable=False)
    Domain: Mapped[str] = mapped_column(Text, nullable=False)

    Units_: Mapped['Units'] = relationship('Units', back_populates='Unit_ShadowReplacements')


class UnitStats(Base):
    __tablename__ = 'Unit_Stats'

    UnitType: Mapped[str] = mapped_column(ForeignKey('Units.UnitType', ondelete='CASCADE', onupdate='CASCADE'), primary_key=True)
    Bombard: Mapped[int] = mapped_column(Integer, nullable=False, server_default=text('0'))
    Combat: Mapped[int] = mapped_column(Integer, nullable=False, server_default=text('0'))
    Range: Mapped[int] = mapped_column(Integer, nullable=False, server_default=text('0'))
    RangedCombat: Mapped[int] = mapped_column(Integer, nullable=False, server_default=text('0'))
    WMDType: Mapped[Optional[str]] = mapped_column(ForeignKey('WMDs.WeaponType', ondelete='CASCADE', onupdate='CASCADE'))

    WMDs_: Mapped[Optional['WMDs']] = relationship('WMDs', back_populates='Unit_Stats')


class UnitTransitionRetains(Base):
    __tablename__ = 'Unit_TransitionRetains'

    UnitType: Mapped[str] = mapped_column(ForeignKey('Units.UnitType', ondelete='CASCADE', onupdate='CASCADE'), primary_key=True)
    IgnoreTraitForReplacement: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=text('0'))


class BarbarianTribeForces(Base):
    __tablename__ = 'BarbarianTribeForces'

    AttackForceType: Mapped[str] = mapped_column(ForeignKey('BarbarianAttackForces.AttackForceType', ondelete='CASCADE', onupdate='CASCADE'), primary_key=True)
    SpecificTribeType: Mapped[Optional[str]] = mapped_column(ForeignKey('BarbarianTribeNames.TribeNameType', ondelete='CASCADE', onupdate='CASCADE'), primary_key=True, nullable=True)
    TribeType: Mapped[Optional[str]] = mapped_column(ForeignKey('BarbarianTribes.TribeType', ondelete='CASCADE', onupdate='CASCADE'), primary_key=True, nullable=True)

    BarbarianAttackForces_: Mapped['BarbarianAttackForces'] = relationship('BarbarianAttackForces', back_populates='BarbarianTribeForces')
    BarbarianTribeNames_: Mapped[Optional['BarbarianTribeNames']] = relationship('BarbarianTribeNames', back_populates='BarbarianTribeForces')
    BarbarianTribes_: Mapped[Optional['BarbarianTribes']] = relationship('BarbarianTribes', back_populates='BarbarianTribeForces')


class ConstructibleGreatPersonPoints(Base):
    __tablename__ = 'Constructible_GreatPersonPoints'

    ConstructibleType: Mapped[str] = mapped_column(ForeignKey('Constructibles.ConstructibleType', ondelete='CASCADE', onupdate='CASCADE'), primary_key=True)
    GreatPersonClassType: Mapped[str] = mapped_column(ForeignKey('GreatPersonClasses.GreatPersonClassType', ondelete='CASCADE', onupdate='CASCADE'), primary_key=True)
    PointsPerTurn: Mapped[int] = mapped_column(Integer, nullable=False, server_default=text('0'))

    Constructibles_: Mapped['Constructibles'] = relationship('Constructibles', back_populates='Constructible_GreatPersonPoints')
    GreatPersonClasses_: Mapped['GreatPersonClasses'] = relationship('GreatPersonClasses', back_populates='Constructible_GreatPersonPoints')


t_ExcludedGreatPersonClasses = Table(
    'ExcludedGreatPersonClasses', Base.metadata,
    Column('GreatPersonClassType', ForeignKey('GreatPersonClasses.GreatPersonClassType', ondelete='CASCADE', onupdate='CASCADE'), primary_key=True),
    Column('TraitType', ForeignKey('Traits.TraitType', ondelete='CASCADE', onupdate='CASCADE'), primary_key=True)
)


class GreatPersonIndividuals(Base):
    __tablename__ = 'GreatPersonIndividuals'

    GreatPersonIndividualType: Mapped[str] = mapped_column(ForeignKey('Types.Type', ondelete='CASCADE', onupdate='CASCADE'), primary_key=True)
    ActionCharges: Mapped[int] = mapped_column(Integer, nullable=False)
    ActionEffectTileHighlighting: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=text('1'))
    ActionRequiresAdjacentBarbarianUnit: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=text('0'))
    ActionRequiresAdjacentMountain: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=text('0'))
    ActionRequiresAdjacentOwnedTile: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=text('0'))
    ActionRequiresAlliedCityStateOwnedTile: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=text('0'))
    ActionRequiresCapital: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=text('0'))
    ActionRequiresCity: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=text('0'))
    ActionRequiresCommander: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=text('0'))
    ActionRequiresForeignCapital: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=text('0'))
    ActionRequiresForeignHemisphere: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=text('0'))
    ActionRequiresForeignTile: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=text('0'))
    ActionRequiresIncompleteSpaceRaceProject: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=text('0'))
    ActionRequiresIncompleteWonder: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=text('0'))
    ActionRequiresIndependentOwnedTile: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=text('0'))
    ActionRequiresMilitaryUnitAnyDomain: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=text('0'))
    ActionRequiresNavigableRiver: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=text('0'))
    ActionRequiresNoMilitaryUnit: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=text('0'))
    ActionRequiresOnOrAdjacentNaturalWonder: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=text('0'))
    ActionRequiresOwnedTile: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=text('1'))
    ActionRequiresPillagedTile: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=text('0'))
    ActionRequiresPlayerRelicSlot: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=text('0'))
    ActionRequiresResource: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=text('0'))
    ActionRequiresTown: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=text('0'))
    ActionRequiresUnownedTile: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=text('0'))
    ActionRequiresValidSettlementLocation: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=text('0'))
    AgeType: Mapped[str] = mapped_column(ForeignKey('Ages.AgeType', ondelete='CASCADE', onupdate='CASCADE'), nullable=False)
    Gender: Mapped[str] = mapped_column(Text, nullable=False)
    GreatPersonClassType: Mapped[str] = mapped_column(ForeignKey('GreatPersonClasses.GreatPersonClassType', ondelete='CASCADE', onupdate='CASCADE'), nullable=False)
    Name: Mapped[str] = mapped_column(Text, nullable=False)
    PercentCostReductionPerLegacyPoint: Mapped[int] = mapped_column(Integer, nullable=False, server_default=text('0'))
    ScaleGoldCostByRelationship: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=text('0'))
    ScaleInfluenceCostByRelationship: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=text('0'))
    Settler: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=text('0'))
    ActionEffectTextOverride: Mapped[Optional[str]] = mapped_column(Text)
    ActionNameTextOverride: Mapped[Optional[str]] = mapped_column(Text)
    ActionRequiresArmyCommanderEmptySlots: Mapped[Optional[int]] = mapped_column(Integer)
    ActionRequiresCityGreatWorkObjectType: Mapped[Optional[str]] = mapped_column(ForeignKey('GreatWorkObjectTypes.GreatWorkObjectType', ondelete='CASCADE', onupdate='CASCADE'))
    ActionRequiresCompletedConstructibleTag: Mapped[Optional[str]] = mapped_column(Text)
    ActionRequiresCompletedConstructibleType: Mapped[Optional[str]] = mapped_column(ForeignKey('Constructibles.ConstructibleType', ondelete='CASCADE', onupdate='CASCADE'))
    ActionRequiresCompletedDistrictType: Mapped[Optional[str]] = mapped_column(ForeignKey('Districts.DistrictType', ondelete='CASCADE', onupdate='CASCADE'))
    ActionRequiresCompletedQuarterType: Mapped[Optional[str]] = mapped_column(ForeignKey('UniqueQuarters.UniqueQuarterType', ondelete='CASCADE', onupdate='CASCADE'))
    ActionRequiresConstructionTypePermission: Mapped[Optional[str]] = mapped_column(ForeignKey('Constructibles.ConstructibleType', ondelete='CASCADE', onupdate='CASCADE'))
    ActionRequiresGoldCost: Mapped[Optional[int]] = mapped_column(Integer)
    ActionRequiresInfluenceCost: Mapped[Optional[int]] = mapped_column(Integer)
    ActionRequiresLessThanXBuildings: Mapped[Optional[int]] = mapped_column(Integer)
    ActionRequiresMilitaryUnitDomain: Mapped[Optional[str]] = mapped_column(Text)
    ActionRequiresNoConstructibleTypeInCity: Mapped[Optional[str]] = mapped_column(ForeignKey('Constructibles.ConstructibleType', ondelete='CASCADE', onupdate='CASCADE'))
    ActionRequiresOnBiomeType: Mapped[Optional[str]] = mapped_column(ForeignKey('Biomes.BiomeType', ondelete='CASCADE', onupdate='CASCADE'))
    ActionRequiresOnOrAdjacentFeatureType: Mapped[Optional[str]] = mapped_column(ForeignKey('Features.FeatureType', ondelete='CASCADE', onupdate='CASCADE'))
    ActionRequiresOnUnitType: Mapped[Optional[str]] = mapped_column(ForeignKey('Units.UnitType', ondelete='CASCADE', onupdate='CASCADE'))
    ActionRequiresResourceType: Mapped[Optional[str]] = mapped_column(ForeignKey('Resources.ResourceType', ondelete='CASCADE', onupdate='CASCADE'))
    ActionRequiresSpecialistCap: Mapped[Optional[int]] = mapped_column(Integer)
    AreaHighlightRadius: Mapped[Optional[int]] = mapped_column(Integer)
    BirthEffectTextOverride: Mapped[Optional[str]] = mapped_column(Text)
    BirthNameTextOverride: Mapped[Optional[str]] = mapped_column(Text)
    ScaleCostsByLegacyPointCardType: Mapped[Optional[str]] = mapped_column(Text)
    UnitType: Mapped[Optional[str]] = mapped_column(ForeignKey('Units.UnitType', ondelete='CASCADE', onupdate='CASCADE'))

    GreatWorkObjectTypes_: Mapped[Optional['GreatWorkObjectTypes']] = relationship('GreatWorkObjectTypes', back_populates='GreatPersonIndividuals')
    Constructibles_: Mapped[Optional['Constructibles']] = relationship('Constructibles', foreign_keys=[ActionRequiresCompletedConstructibleType], back_populates='GreatPersonIndividuals')
    Districts_: Mapped[Optional['Districts']] = relationship('Districts', back_populates='GreatPersonIndividuals')
    UniqueQuarters_: Mapped[Optional['UniqueQuarters']] = relationship('UniqueQuarters', back_populates='GreatPersonIndividuals')
    Constructibles1: Mapped[Optional['Constructibles']] = relationship('Constructibles', foreign_keys=[ActionRequiresConstructionTypePermission], back_populates='GreatPersonIndividuals_')
    Constructibles2: Mapped[Optional['Constructibles']] = relationship('Constructibles', foreign_keys=[ActionRequiresNoConstructibleTypeInCity], back_populates='GreatPersonIndividuals1')
    Biomes_: Mapped[Optional['Biomes']] = relationship('Biomes', back_populates='GreatPersonIndividuals')
    Features_: Mapped[Optional['Features']] = relationship('Features', back_populates='GreatPersonIndividuals')
    Units_: Mapped[Optional['Units']] = relationship('Units', foreign_keys=[ActionRequiresOnUnitType], back_populates='GreatPersonIndividuals')
    Resources_: Mapped[Optional['Resources']] = relationship('Resources', back_populates='GreatPersonIndividuals')
    Ages_: Mapped['Ages'] = relationship('Ages', back_populates='GreatPersonIndividuals')
    GreatPersonClasses_: Mapped['GreatPersonClasses'] = relationship('GreatPersonClasses', back_populates='GreatPersonIndividuals')
    Units1: Mapped[Optional['Units']] = relationship('Units', foreign_keys=[UnitType], back_populates='GreatPersonIndividuals_')
    GreatPersonIndividualActionModifiers: Mapped[list['GreatPersonIndividualActionModifiers']] = relationship('GreatPersonIndividualActionModifiers', back_populates='GreatPersonIndividuals_')
    GreatPersonIndividualBirthModifiers: Mapped[list['GreatPersonIndividualBirthModifiers']] = relationship('GreatPersonIndividualBirthModifiers', back_populates='GreatPersonIndividuals_')
    GreatWorks: Mapped[list['GreatWorks']] = relationship('GreatWorks', back_populates='GreatPersonIndividuals_')


class MapGreatPersonClasses(Base):
    __tablename__ = 'Map_GreatPersonClasses'

    GreatPersonClassType: Mapped[str] = mapped_column(ForeignKey('GreatPersonClasses.GreatPersonClassType', ondelete='CASCADE', onupdate='CASCADE'), primary_key=True)
    MapSizeType: Mapped[str] = mapped_column(ForeignKey('Maps.MapSizeType', ondelete='CASCADE', onupdate='CASCADE'), primary_key=True)
    MaxWorldInstances: Mapped[Optional[int]] = mapped_column(Integer)

    GreatPersonClasses_: Mapped['GreatPersonClasses'] = relationship('GreatPersonClasses', back_populates='Map_GreatPersonClasses')
    Maps_: Mapped['Maps'] = relationship('Maps', back_populates='Map_GreatPersonClasses')


class ProjectGreatPersonPoints(Base):
    __tablename__ = 'Project_GreatPersonPoints'

    GreatPersonClassType: Mapped[str] = mapped_column(ForeignKey('GreatPersonClasses.GreatPersonClassType', ondelete='CASCADE', onupdate='CASCADE'), primary_key=True)
    ProjectType: Mapped[str] = mapped_column(ForeignKey('Projects.ProjectType', ondelete='CASCADE', onupdate='CASCADE'), primary_key=True)
    PointProgressionModel: Mapped[str] = mapped_column(Text, nullable=False, server_default=text('"NO_PROGRESSION_MODEL"'))
    PointProgressionParam1: Mapped[int] = mapped_column(Integer, nullable=False, server_default=text('0'))
    Points: Mapped[int] = mapped_column(Integer, nullable=False, server_default=text('0'))

    GreatPersonClasses_: Mapped['GreatPersonClasses'] = relationship('GreatPersonClasses', back_populates='Project_GreatPersonPoints')
    Projects_: Mapped['Projects'] = relationship('Projects', back_populates='Project_GreatPersonPoints')


class VisArtIndependentBuildingCultures(Base):
    __tablename__ = 'VisArt_IndependentBuildingCultures'

    BuildingCulture: Mapped[str] = mapped_column(Text, primary_key=True)
    IndependentType: Mapped[str] = mapped_column(ForeignKey('Independents.IndependentType', ondelete='CASCADE', onupdate='CASCADE'), primary_key=True)

    Independents_: Mapped['Independents'] = relationship('Independents', back_populates='VisArt_IndependentBuildingCultures')


class VisArtIndependentUnitCultures(Base):
    __tablename__ = 'VisArt_IndependentUnitCultures'

    IndependentType: Mapped[str] = mapped_column(ForeignKey('Independents.IndependentType', ondelete='CASCADE', onupdate='CASCADE'), primary_key=True)
    UnitCulture: Mapped[str] = mapped_column(Text, primary_key=True)

    Independents_: Mapped['Independents'] = relationship('Independents', back_populates='VisArt_IndependentUnitCultures')


class GreatPersonIndividualActionModifiers(Base):
    __tablename__ = 'GreatPersonIndividualActionModifiers'

    GreatPersonIndividualType: Mapped[str] = mapped_column(ForeignKey('GreatPersonIndividuals.GreatPersonIndividualType', ondelete='CASCADE', onupdate='CASCADE'), primary_key=True)
    ModifierId: Mapped[str] = mapped_column(Text, primary_key=True)
    AttachmentTargetType: Mapped[str] = mapped_column(Text, nullable=False, server_default=text('"GREAT_PERSON_ACTION_ATTACHMENT_TARGET_PLAYER"'))

    GreatPersonIndividuals_: Mapped['GreatPersonIndividuals'] = relationship('GreatPersonIndividuals', back_populates='GreatPersonIndividualActionModifiers')


class GreatPersonIndividualBirthModifiers(Base):
    __tablename__ = 'GreatPersonIndividualBirthModifiers'

    GreatPersonIndividualType: Mapped[str] = mapped_column(ForeignKey('GreatPersonIndividuals.GreatPersonIndividualType', ondelete='CASCADE', onupdate='CASCADE'), primary_key=True)
    ModifierId: Mapped[str] = mapped_column(Text, primary_key=True)

    GreatPersonIndividuals_: Mapped['GreatPersonIndividuals'] = relationship('GreatPersonIndividuals', back_populates='GreatPersonIndividualBirthModifiers')


class GreatPersonVictoryTypeEntries(Base):
    __tablename__ = 'GreatPersonVictoryTypeEntries'

    GreatPersonIndividualType: Mapped[str] = mapped_column(ForeignKey('GreatPersonIndividuals.GreatPersonIndividualType', ondelete='CASCADE', onupdate='CASCADE'), primary_key=True)
    GreatPersonVictorySource: Mapped[str] = mapped_column(Text, nullable=False, server_default=text('"NO_VICTORY"'))
    MaxPointsPerUse: Mapped[int] = mapped_column(Integer, nullable=False, server_default=text('0'))
    Points: Mapped[int] = mapped_column(Integer, nullable=False, server_default=text('0'))
    VictoryType: Mapped[str] = mapped_column(Text, nullable=False, server_default=text('"NO_GREAT_PERSON_VICTORY_SOURCE"'))


class GreatWorks(Base):
    __tablename__ = 'GreatWorks'

    GreatWorkType: Mapped[str] = mapped_column(Text, primary_key=True)
    Generic: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=text('1'))
    GreatWorkObjectType: Mapped[str] = mapped_column(ForeignKey('GreatWorkObjectTypes.GreatWorkObjectType', ondelete='RESTRICT', onupdate='CASCADE'), nullable=False)
    Name: Mapped[str] = mapped_column(Text, nullable=False)
    AgeType: Mapped[Optional[str]] = mapped_column(ForeignKey('Ages.AgeType', ondelete='CASCADE', onupdate='CASCADE'))
    Audio: Mapped[Optional[str]] = mapped_column(Text)
    Description: Mapped[Optional[str]] = mapped_column(Text)
    GreatPersonIndividualType: Mapped[Optional[str]] = mapped_column(ForeignKey('GreatPersonIndividuals.GreatPersonIndividualType', ondelete='CASCADE', onupdate='CASCADE'))
    GreatWorkSourceType: Mapped[Optional[str]] = mapped_column(ForeignKey('GreatWorkSourceTypes.GreatWorkSourceType', ondelete='RESTRICT', onupdate='CASCADE'))
    Image: Mapped[Optional[str]] = mapped_column(Text)
    Quote: Mapped[Optional[str]] = mapped_column(Text)

    Ages_: Mapped[Optional['Ages']] = relationship('Ages', back_populates='GreatWorks')
    GreatPersonIndividuals_: Mapped[Optional['GreatPersonIndividuals']] = relationship('GreatPersonIndividuals', back_populates='GreatWorks')
    GreatWorkObjectTypes_: Mapped['GreatWorkObjectTypes'] = relationship('GreatWorkObjectTypes', back_populates='GreatWorks')
    GreatWorkSourceTypes_: Mapped[Optional['GreatWorkSourceTypes']] = relationship('GreatWorkSourceTypes', back_populates='GreatWorks')
    GreatWorkModifiers: Mapped[list['GreatWorkModifiers']] = relationship('GreatWorkModifiers', back_populates='GreatWorks_')
    GreatWork_YieldChanges: Mapped[list['GreatWorkYieldChanges']] = relationship('GreatWorkYieldChanges', back_populates='GreatWorks_')


class GreatWorkModifiers(Base):
    __tablename__ = 'GreatWorkModifiers'

    GreatWorkType: Mapped[str] = mapped_column(ForeignKey('GreatWorks.GreatWorkType', ondelete='CASCADE', onupdate='CASCADE'), primary_key=True)
    ModifierID: Mapped[str] = mapped_column(Text, primary_key=True)

    GreatWorks_: Mapped['GreatWorks'] = relationship('GreatWorks', back_populates='GreatWorkModifiers')


class GreatWorkYieldChanges(Base):
    __tablename__ = 'GreatWork_YieldChanges'

    GreatWorkType: Mapped[str] = mapped_column(ForeignKey('GreatWorks.GreatWorkType', ondelete='CASCADE', onupdate='CASCADE'), primary_key=True)
    YieldType: Mapped[str] = mapped_column(ForeignKey('Yields.YieldType', ondelete='CASCADE', onupdate='CASCADE'), primary_key=True)
    YieldChange: Mapped[int] = mapped_column(Integer, nullable=False)

    GreatWorks_: Mapped['GreatWorks'] = relationship('GreatWorks', back_populates='GreatWork_YieldChanges')
    Yields_: Mapped['Yields'] = relationship('Yields', back_populates='GreatWork_YieldChanges')
