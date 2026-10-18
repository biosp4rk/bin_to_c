// 0x0
const s8 S8_Dec_00[8] = {
    0,
    1,
    2,
    3,
    4,
    5,
    6,
    7
};

// 0x8
const s8 S8_Dec_08[8] = {
    -1,
    -2,
    -3,
    -4,
    -5,
    -6,
    -7,
    -8
};

// 0x0
const u8 U8_Hex_00[8] = { 0x0, 0x1, 0x2, 0x3, 0x4, 0x5, 0x6, 0x7 };

// 0x8
const u8 U8_Hex_08[8] = { 0xFF, 0xFE, 0xFD, 0xFC, 0xFB, 0xFA, 0xF9, 0xF8 };

// 0x10
const s8 Ascii_10[13] = "Example text";

// 0x8
const u8 EnumVal_08[4] = {
    [INDEX_0] = 0xFF,
    [INDEX_1] = 0xFE,
    [INDEX_2] = 0xFD,
    [INDEX_3] = 0xFC
};

// 0x0
const u8 DiffItems_00[3] = {
    [0] = FOO_0,
    [1] = BAR_1,
    [2] = 2
};

// 0x20
const struct MyStruct Struct_20[2] = {
    {
        .pData = (const u8*)0x8000100,
        .flag = TRUE
    },
    {
        .pData = (const u8*)0x8000200,
        .flag = FALSE
    }
};
