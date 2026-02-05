# bin_to_c

bin_to_c is a python script intended for extracting binary data from GBA ROMs into formatted C code. This allows automatic extraction of complex data types, with support for a variety of formatting options, including:

- Decimal vs hexadecimal integers
- Enum values
- Single-line vs multi-line arrays
- ASCII strings
- Pointer names


## Contents
- [Usage](#usage)
- [Input File Format](#input-file-format)
  - [Top-Level Structure](#top-level-structure)
  - [`def` Property](#def-property)
  - [Type Definition Object](#type-definition-object)
  - [`items` Property](#items-property)
  - [Integer Values](#integer-values)
- [Context File Format](#context-file-format)
  - [Top-Level Structure](#top-level-structure-1)
  - [`enums` Property](#enums-property)
  - [Enum Definition Object](#enum-definition-object)
  - [`defs` Property](#defs-property)
- [Symbols File Format](#symbols-file-format)
- [Outputting Pointers](#outputting-pointers)
- [Examples](#examples)
- [Direct Python Input](#direct-python-input)
- [Planned Features](#planned-features)


## Usage

```
python3 bin_to_c.py rom_file input_file [-c CONTEXT_FILE] [-s SYMBOLS_FILE] [-p PTR_OUTPUT]
```

**Required arguments:**
- `rom_file`: Path to a ROM file (or binary file) to extract data from
- `input_file`: Path to an input JSON file, which specifies the data to extract and the format to use (see [Input File Format](#input-file-format))

**Optional arguments:**
- `-c CONTEXT_FILE`: Path to a context JSON file, containing enum and type definitions (see [Context File Format](#context-file-format))
- `-s SYMBOLS_FILE`: Path to a symbols file, containing addresses and their names (see [Symbols File Format](#symbols-file-format))
- `-p PTR_OUTPUT`: The output path to write all pointers that were encountered (see [Outputting Pointers](#outputting-pointers))


## Input File Format

### Top-Level Structure

The root value is an array. Each element in the array is an object with the following shape:

```json
{
  "arrays": <true|false>,
  "def": ...,
  "decl": "const MyType",
  "items": [...]
}
```

#### Required Properties

| Property | Type             | Description                                                     |
| -------- | ---------------- | --------------------------------------------------------------- |
| `def`    | object or string | A type definition, or the name of a type defined in the context |
| `items`  | array            | List of items to extract, all sharing the same type             |

#### Optional Properties

| Property | Type    | Description                                                                   |
| -------- | ------- | ----------------------------------------------------------------------------- |
| `arrays` | boolean | Indicates that each item is an array with the provided count (default: false) |
| `decl`   | string  | Optional declaration string to insert before each item                        |

---

### `def` Property

The `def` property specifies a type definition. It can be either:

#### 1. A Type Name

The name of a type definition from the context file (see [Context File Format](#context-file-format)):

```json
"def": "MyStruct"
```

#### 2. A Type Definition Object

An object describing a type definition. The exact structure depends on the `kind` field.

---

### Type Definition Object

Each type definition object must include a `kind` field that determines its shape. Possible kinds include [`int`](#integer), [`bool`](#boolean), [`enum_val`](#enum-value), [`pointer`](#pointer), [`array`](#array), and [`struct`](#struct).

#### Integer

Integers can be 8, 16, or 32 bit, signed or unsigned, and represented using decimal or hexidecimal.

```json
{
  "kind": "int",
  "type": "u8",
  "base": "hex"
}
```

| Field  | Description                                   |
| ------ | --------------------------------------------- |
| `type` | One of `u8`, `u16`, `u32`, `s8`, `s16`, `s32` |
| `base` | Optional: `dec` or `hex` (default: `dec`)     |

---

#### Boolean

Boolean is intended for integers that should be represented as either `TRUE` or `FALSE`. The only valid values for booleans are 0 (`FALSE`) or 1 (`TRUE`).

```json
{
  "kind": "bool",
  "size": 1
}
```

| Field  | Description                             |
| ------ | --------------------------------------- |
| `size` | Integer size in bytes: `1`, `2`, or `4` |

---

#### Enum Value

This is intended for integers that should be represented as enum value names. `enum_def` can be a full enum definition, or the name of an enum definition from the context file (see [Enum Definition Object](#enum-definition-object)).

```json
{
  "kind": "enum_val",
  "size": 2,
  "enum_def": "MyEnum"
}
```

| Field      | Description                             |
| ---------- | --------------------------------------- |
| `size`     | Integer size in bytes: `1`, `2`, or `4` |
| `enum_def` | Enum name or full enum definition       |


---

#### Pointer

Pointers are expected to be 4 bytes and in the ROM address space (starting at 0x8000000). If a symbols file is provided, pointers can be replaced with a symbol name (see [Symbols File Format](#symbols-file-format)). An optional type cast can be specified for cases when no symbols are provided or no name is found. If no type cast is provided, `void*` will be used by default. Any pointers encountered are tracked and can be output to a file (see [Outputting Pointers](#outputting-pointers)).

```json
{
  "kind": "pointer",
  "type_cast": "const MyType*"
}
```

| Field       | Description                                             |
| ----------- | ------------------------------------------------------- |
| `type_cast` | Optional type cast (if the pointer name isn't resolved) |

---

#### Array

Arrays are defined by providing a count, an item type definition (or list of definitions), and an optional format. If `items` is a type definition, then all items in the array will use that type. If `items` is a list of types, then each item in the array can have a different type (the length of `items` must match the count). There are a few possible formats for the array, detailed below.

```json
{
  "kind": "array",
  "count": 4,
  "items": { "kind": "int", "type": "u8" }
}
```

| Field      | Description                                     |
| ---------- | ----------------------------------------------- |
| `count`    | Number of elements (integer or hex string)      |
| `items`    | Item type or list of item types                 |
| `format`   | Optional display format (default: `multi_line`) |
| `enum_def` | Optional enum definition for indexing           |

Supported formats:

- `single_line`: All items on a single line (can't be used with structs or arrays)
- `multi_line`: Each item on its own line
- `int_index`: Designated initializer list with integers
- `enum_index`: Designated initializer list with enum value names
- `ascii`: ASCII string (can only be used with S8 or U8 integers)

If the format is set to `enum_index`, then `enum_def` needs to be provided.

---

#### Struct

Structs consist of an array of fields, where each field has a name and a type. The type can be any type definition, specified with a type name or a full type definition.

```json
{
  "kind": "struct",
  "fields": [
    {
      "name": "field1",
      "type": "MyType"
    },
    {
      "name": "field2",
      "type": { "kind": "int", "type": "u8" }
    }
  ]
}
```

| Field         | Description                       |
| ------------- | --------------------------------- |
| `fields`      | Array of struct fields            |
| `fields.name` | Field name                        |
| `fields.type` | Type name or full type definition |

---

### `items` Property

The `items` property is an array describing the items to extract. If the top-level `arrays` property is `true`, then each item will be considered an array and `count` must be specified.

```json
{
  "addr": "0x10",
  "name": "myVar",
  "count": 4
}
```

#### Required Fields

| Field  | Description                     |
| ------ | ------------------------------- |
| `addr` | Address (integer or hex string) |


#### Optional Fields

| Field   | Description                |
| ------- | -------------------------- |
| `name`  | Item name to use in output |
| `count` | Number of items in array   |

---

### Integer Values

Several fields (`addr`, `count`) accept integer values in multiple forms:

* JSON number: `16`
* Decimal string: `"16"`
* Hex string: `"0x10"`


## Context File Format

Context files define enums and types that can be used in combination with input files. This makes it easier to reuse enums and types, and also helps reduce the size of input file definitions. 

### Top-Level Structure

The root value is an object with the following properties (both are optional):

```json
{
  "enums": {...},
  "defs": {...}
}
```

---

### `enums` Property

The `enums` property is an object with enum names as keys and enum definitions as values.

```json
{
  "MyFirstEnum": ...,
  "MySecondEnum": ...
}
```

---

### Enum Definition Object

Enum definitions are either:

#### 1. An Array of Names

The first name is assigned 0, and each subsequent name is assigned a value 1 higher (the same way it works in C).

```json
[
  "VAL_0",
  "VAL_1",
  "VAL_2"
]
```

#### 2. An Object of Value/Name Pairs

Each key is the value assigned to each name. Note that JSON keys cannot be integers, but you can use decimal or hex strings.

```json
{
  "1": "VAL_1",
  "3": "VAL_3",
  "7": "VAL_7"
}
```

---

### `defs` Property

The `defs` property is an object with type names as keys and type definitions as values. For an overview of type definitions, see [Type Definition Object](#type-definition-object).

```json
{
  "MyFirstType": {
    "kind": "int",
    ...
  },
  "MySecondType": {
    "kind": "struct",
    ...
  }
}
```

## Symbols File Format

A symbols file contains addresses and symbol names, which can be used to replace any matching pointers with the provided name. Each line should contain a hex address and a name, separated by whitespace. Empty lines are ignored. Comments are supported and start with `;`.

```
; My symbols
08000100 Data1
08000200 Data2
```


## Outputting Pointers

If a pointer output filename is provided, any pointers encountered will be written to the provided file. The pointers are sorted with one pointer per line. Each pointer is followed by a description of every variable, field, or array index with that pointer. This is helpful for assigning names to pointers (which can be added to a symbols file).

Example output for `struct MyStruct MyData[4]`, where the struct has a pointer field named `pData`:

```
8000010	MyData,3,pData,const u16*
8000020	MyData,0,pData,const u16*; MyData,2,pData,const u16*
8000030	MyData,1,pData,const u16*
```


## Examples

Here's an example of a struct which contains one of each data type.

Input:

```json
[
  {
    "def": {
      "kind": "struct",
      "fields": [
        {
          "name": "myInt",
          "type": { "kind": "int", "type": "s8" }
        },
        {
          "name": "myBool",
          "type": { "kind": "bool", "size": 1 }
        },
        {
          "name": "myEnum",
          "type": {
            "kind": "enum_val",
            "size": 1,
            "enum_def": { "0x10": "VAL_10" }
          }
        },
        {
          "name": "myPtr",
          "type": { "kind": "pointer", "type_cast": "const u16*" }
        },
        {
          "name": "myArray",
          "type": {
            "kind": "array",
            "count": 4,
            "items": { "kind": "int", "type": "u8" },
            "format": "single_line"
          }
        }
      ]
    },
    "decl": "const struct MyStruct",
    "items": [
      {"addr": "0x100", "name": "MyData"}
    ]
  }
]
```

Output:

```c
// 0x100
const struct MyStruct MyData = {
    .myInt = -1,
    .myBool = TRUE,
    .myEnum = VAL_10,
    .myPtr = (const u16*)0x8000100,
    .myArray = { 1, 2, 3, 4 }
};
```

There are also a variety of examples in the `examples/` directory.


## Direct Python Input

If you prefer, the input can be written directly in python. The code in `direct.py` provides a template for doing so. This can be easier/quicker than writing JSON, especially if your IDE has autocomplete and type checking.

Here's the example above written in python:

```python
DataItem(
    Struct([
        ("myInt", Integer(IntType.S8)),
        ("myBool", Boolean(1)),
        ("myEnum", EnumVal(1, {0x10: "VAL_10"})),
        ("myPtr", Pointer("const u16*")),
        ("myArray", Array(
            4, Integer(IntType.U8), ArrFormat.SINGLE_LINE
        ))
    ]),
    0x100, "MyData", "const struct MyStruct"
)
```


## Planned Features

- Validation using JSON schema
- Support enum flag values (with OR operators)
- Examples
  - Add more complex examples
  - Add examples with symbols files
