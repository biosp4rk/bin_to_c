// 0x0
const struct DemoRam sDemoRam[3] = {
    [DEMO_ID_SECTOR_2] = {
        .area = AREA_SECTOR_2,
        .lastDoorUsed = 20,
        .securityLevel = SECURITY_LEVEL_1,
        .downloadedMaps = 0x7,
        .event = EVENT_BOMB_DATA_DOWNLOADED,
        .soundEvent = SOUND_EVENT_FIRST_CONVERSATION_STARTED,
        .abilityCount = ABILITY_COUNT_BOMBS,
        .maxEnergy = 399,
        .currentEnergy = 246,
        .maxMissiles = 35,
        .currentMissiles = 32,
        .maxPowerBombs = 10,
        .currentPowerBombs = 10,
        .samusDirection = KEY_LEFT,
        .samusX = 1864,
        .samusY = 1279
    },
    [DEMO_ID_SECTOR_5] = {
        .area = AREA_SECTOR_5,
        .lastDoorUsed = 49,
        .securityLevel = SECURITY_LEVEL_3,
        .downloadedMaps = 0x7F,
        .event = EVENT_ICE_MISSILE_DATA_DOWNLOADED,
        .soundEvent = SOUND_EVENT_FIRST_CONVERSATION_STARTED,
        .abilityCount = ABILITY_COUNT_ICE_MISSILES,
        .maxEnergy = 799,
        .currentEnergy = 432,
        .maxMissiles = 75,
        .currentMissiles = 48,
        .maxPowerBombs = 10,
        .currentPowerBombs = 10,
        .samusDirection = KEY_RIGHT,
        .samusX = 344,
        .samusY = 3775
    },
    [DEMO_ID_SECTOR_4] = {
        .area = AREA_SECTOR_4,
        .lastDoorUsed = 15,
        .securityLevel = SECURITY_LEVEL_1,
        .downloadedMaps = 0xF,
        .event = EVENT_NAVIGATION_ROOM_ENTERING_AQA,
        .soundEvent = SOUND_EVENT_FIRST_CONVERSATION_STARTED,
        .abilityCount = ABILITY_COUNT_HIGH_JUMP,
        .maxEnergy = 499,
        .currentEnergy = 352,
        .maxMissiles = 50,
        .currentMissiles = 42,
        .maxPowerBombs = 10,
        .currentPowerBombs = 10,
        .samusDirection = KEY_LEFT,
        .samusX = 1840,
        .samusY = 575
    }
};

// 0x54
const struct AbilityRamValue sAbilityRamValues[4] = {
    [ABILITY_COUNT_NONE] = {
        .beamStatus = 0,
        .weaponStatus = 0,
        .suitStatus = 0,
        .isSuit = FALSE,
        .messageNumber = MESSAGE_LEVEL_1,
        .soundEvent = SOUND_EVENT_FIRST_CONVERSATION_STARTED
    },
    [ABILITY_COUNT_MISSILES] = {
        .beamStatus = 0,
        .weaponStatus = MBF_MISSILES,
        .suitStatus = 0,
        .isSuit = FALSE,
        .messageNumber = MESSAGE_MISSILE_DATA,
        .soundEvent = SOUND_EVENT_DOWNLOADED_MISSILES
    },
    [ABILITY_COUNT_MORPH_BALL] = {
        .beamStatus = 0,
        .weaponStatus = 0,
        .suitStatus = SMF_MORPH_BALL,
        .isSuit = FALSE,
        .messageNumber = MESSAGE_MORPH_BALL,
        .soundEvent = SOUND_EVENT_MORPH_BALL_ABILITY_RECOVERED
    },
    [ABILITY_COUNT_CHARGE_BEAM] = {
        .beamStatus = BF_CHARGE_BEAM,
        .weaponStatus = 0,
        .suitStatus = 0,
        .isSuit = FALSE,
        .messageNumber = MESSAGE_CHARGE_BEAM,
        .soundEvent = SOUND_EVENT_CHARGE_BEAM_ABILITY_RECOVERED
    }
};
