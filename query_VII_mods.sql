SELECT DISTINCT
  T_Mods.ModId,
  T_Items.Item AS ExecutedFile
FROM
  Mods AS T_Mods
  LEFT JOIN ModProperties AS T_ModProps
    ON T_Mods.ModRowId = T_ModProps.ModRowId
    AND T_ModProps.Name = 'LoadOrder'
  JOIN ActionGroups AS T_ActionGroups
    ON T_Mods.ModRowId = T_ActionGroups.ModRowId
  LEFT JOIN ActionGroupProperties AS T_ActionGroupProps
    ON T_ActionGroups.ActionGroupRowId = T_ActionGroupProps.ActionGroupRowId
    AND T_ActionGroupProps.Name = 'LoadOrder'
  JOIN Actions AS T_Actions
    ON T_ActionGroups.ActionGroupRowId = T_Actions.ActionGroupRowId
  JOIN ActionItems AS T_Items
    ON T_Actions.ActionRowId = T_Items.ActionRowId
  LEFT JOIN Criteria AS T_Criteria
    ON T_ActionGroups.CriteriaRowId = T_Criteria.CriteriaRowId
  LEFT JOIN Criterion C
    ON T_Criteria.CriteriaRowId = C.CriteriaRowId
  LEFT JOIN CriterionProperties CP
    ON C.CriterionRowId = CP.CriterionRowId
WHERE
  T_Mods.Disabled IS NOT 1
  AND T_Actions.ActionType = 'UpdateDatabase'
  AND T_ActionGroups.Scope = 'game'
  AND (
    T_ActionGroups.CriteriaRowId IS NULL
    OR (
      T_Criteria.Any = 0
      AND NOT EXISTS (
        SELECT 1
        FROM Criterion C2
        LEFT JOIN CriterionProperties CP2 ON C2.CriterionRowId = CP2.CriterionRowId
        WHERE C2.CriteriaRowId = T_Criteria.CriteriaRowId
          AND NOT (
            (C2.CriterionType = 'AlwaysMet')
            OR (C2.CriterionType = 'AgeInUse'
                AND CP2.Name = 'Value'
                AND CP2.Value = 'AGE_ANTIQUITY')
            OR (C2.CriterionType = 'ModInUse'
                AND (C2.Inverse = 0 OR C2.Inverse IS NULL)
                AND EXISTS (
                  SELECT 1 FROM Mods M
                  WHERE M.ModId = CP2.Value
                    AND (M.Disabled IS NULL OR M.Disabled = 0)
                )
            )
            OR (C2.CriterionType = 'ModInUse'
                AND C2.Inverse = 1
                AND NOT EXISTS (
                  SELECT 1 FROM Mods M
                  WHERE M.ModId = CP2.Value
                    AND (M.Disabled IS NULL OR M.Disabled = 0)
                )
            )
          )
      )
    )
    OR (
      T_Criteria.Any = 1
      AND EXISTS (
        SELECT 1
        FROM Criterion C2
        LEFT JOIN CriterionProperties CP2 ON C2.CriterionRowId = CP2.CriterionRowId
        WHERE C2.CriteriaRowId = T_Criteria.CriteriaRowId
          AND (
            (C2.CriterionType = 'AlwaysMet')
            OR (C2.CriterionType = 'AgeInUse'
                AND CP2.Name = 'Value'
                AND CP2.Value = 'AGE_ANTIQUITY')
            OR (C2.CriterionType = 'ModInUse'
                AND (C2.Inverse = 0 OR C2.Inverse IS NULL)
                AND EXISTS (
                  SELECT 1 FROM Mods M
                  WHERE M.ModId = CP2.Value
                    AND (M.Disabled IS NULL OR M.Disabled = 0)
                )
            )
            OR (C2.CriterionType = 'ModInUse'
                AND C2.Inverse = 1
                AND NOT EXISTS (
                  SELECT 1 FROM Mods M
                  WHERE M.ModId = CP2.Value
                    AND (M.Disabled IS NULL OR M.Disabled = 0)
                )
            )
          )
      )
    )
  )
ORDER BY
  CAST(COALESCE(T_ModProps.Value, '0') AS INTEGER),
  CAST(COALESCE(T_ActionGroupProps.Value, '0') AS INTEGER),
  T_Mods.ModRowId,
  T_ActionGroups.ActionGroupRowId,
  T_Actions.ActionRowId,
  T_Items.Arrangement;