SELECT DISTINCT ModId, OtherModId as DependsOn FROM ModRelationships JOIN Mods AS T_Mods
       JOIN ActionGroups ON ActionGroups.ModRowId = T_Mods.ModRowId
         WHERE Relationship='Dependency';