x = 6
console.log(x)

function a(y)
{
    return x+y
}

function b(y)
{
    return x + a(y)
}

console.log(a(4))
console.log(b(3))
console.log(x)