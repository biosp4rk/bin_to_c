// 0x0
const struct MyStruct1 MyStruct1_00 = {
    .field1 = 0x12,
    .field2 = 0x1234,
    .field3 = 0x12345678,
    .field4 = FALSE,
    .field5 = TRUE
};

// 0x10
const struct MyStruct2 MyStruct2_10 = {
    .myArray = {
        [0] = {
            .pData = (const u16*)0x8000010,
            .varX = 1,
            .varY = 2
        },
        [1] = {
            .pData = (const u16*)0x8000020,
            .varX = 3,
            .varY = 4
        },
        [2] = {
            .pData = (const u16*)0x8000030,
            .varX = 5,
            .varY = 6
        }
    },
    .pInfo = (const MyStruct1*)0x8000040
};
