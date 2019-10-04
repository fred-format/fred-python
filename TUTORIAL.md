# FRED Format

FRED is a data representation format akin to JSON used to author, exchange,
and store information. FRED extends JSON with new syntax and datatypes and is
very simple to use once you are familiar with JSON.

This tutorial walks through the main features of the language and suggests best
practices both in terms of usage and style. We start with a brief description
of JSON and show the novel features that FRED introduces.


## FRED as a better JSON

Anyone who uses JavaScript, Python and similar languages should appreciate the
simplicity of JSON: it reifies a common notation and use it as
an exchange format to represent data in a language-agnostic way.

The structure bellow

```
{
    "name": "Alan Turing",
    "birthday": "1912-06-23",
    "awards": [
        "Order of the British Empire, 1946",
        "Fellow of the Royal Society, 1951"
    ]
}
```

is valid JSON, ECMAScript, Python and probably a valid syntax of a dozen other
languages.


1st Problem: commas

```
{ "name": "Alan Turing"
, "birthday": "1912-06-23"
, "awards":
    [ "Order of the British Empire, 1946"
    , "Fellow of the Royal Society, 1951"
    ]
}
```


```
{
    name: "Alan Turing"
    birthday: "1912-06-23"
    awards: [
        "Order of the British Empire, 1946"
        "Fellow of the Royal Society, 1951"
    ]
}
```

```
Person {
    name: "Alan Turing"
    birthday: 1912-06-23
    awards: [
        Award (year=1946) "Order of the British Empire"
        Award (year=1951) "Fellow of the Royal Society"
    ]
}
```

```
Person {
    name: "Alan Turing"
    birthday: 1912-06-23
    awards: [
        (Award year=1946
               where="England"
               ref/wikipedia="https://en.wikipedia.org/wiki/Order_of_the_British_Empire"
            "Order of the British Empire")

        (Award year=1946
               where="England"
               ref/wikipedia="https://en.wikipedia.org/wiki/Order_of_the_British_Empire"
            "Order of the British Empire")

        (Award location="England"
               ref/wikipedia="https://en.wikipedia.org/wiki/Order_of_the_British_Empire"
            {
                description:"Order of the British Empire"
                year: 1946
            })

        Award (year=1951) "Fellow of the Royal Society"
    ]
}
```




Award("Order of the British Empire", year=1946)
new Award("Order of the British Empire", {year: 1946})



