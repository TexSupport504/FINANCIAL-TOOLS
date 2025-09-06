# Page 14

EXAMPLES
Using the floor function in for example excel, you take the
current price, divide it by the power of three number, and you
only take the integer part, ignoring the fractional part.
curren po3 floor(current Dealing
t price number price / po3 range
number) low
12345 243 50 12150
40328 81 497 40257
23589 2187 12150 21870
Now we have our dealing range low, we can calculate the
dealing range high.
We just take the dealing range low and add the power of
three number we used in our formula above to it.
So let’s say we are calculating the dealing range high for
our EURUSD asset.
We determined above that the PO3 dealing range low for
our 243 PO3 range was 12150.
We add the 243 PO3 number to it, and we get a dealing
range high of 12150+243 = 12393