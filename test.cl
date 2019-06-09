class A {
    a: Int <- 3;
    suma(a: Int, b: Int): Int {
        a + b
    };
    b: Int;
};

class B inherits A {
    c: A <- new A;
    f(d: Int, a: A): String { {
        isvoid d;
        f(1, new A);
        let f: Int <- 1 in { 
            8;
            if not 5 <= 20 then f * 34 + ~1 else 43 / f + 12 fi;
        };
        c <- new A.suma(5, f);
        c;
    } };
    z: Bool <- false;
};

class Point {
    x : AUTO_TYPE;
    y : AUTO_TYPE;
    z : AUTO_TYPE <- 1;
    init(n : Int, m : Int) : SELF_TYPE { {
        x <- n;
        y <- m;
        self;
    } };
};

class Main inherits IO {
    main(): Object { {
        out_string("Enter an integer greater-than or equal-to 0: ");

        let input: Int <- in_int() in
        if input < 0 then
            out_string("ERROR: Number must be greater-than or equal-to 0\\n")
        else {
            out_string("The factorial of ").out_int(input);
            out_string(" is ").out_int(factorial(input));
            out_string("\\n");
        }
        fi;
    } };

    out_string(y: Int): SELF_TYPE { 3 };

    test() : AUTO_TYPE {
        let x : AUTO_TYPE <- 3 + 2 in {
            case x of
                y : Int => out_string("Ok");
                w : SELF_TYPE => out_string("Wrong!");
            esac;
        }
    };

    factorial(num: AUTO_TYPE): AUTO_TYPE {
        if num = 0 then 1 else num * factorial(num - 1) fi
    };

    ackermann(m : AUTO_TYPE, n: AUTO_TYPE) : AUTO_TYPE {
        if (m=0) then n+1 else
            if (n=0) then ackermann(m-1, 1) else
                ackermann(m-1, ackermann(m, n-1))
            fi
        fi
    };

    f(a: AUTO_TYPE, b: AUTO_TYPE) : AUTO_TYPE {
        if (a=1) then b else
            g(a + 1, b/2)
        fi
    };

    g(a: AUTO_TYPE, b: AUTO_TYPE) : AUTO_TYPE {
        if (b=1) then a else
            f(a/2, b+1)
        fi
    };
};

class A1 inherits A2 { w(ww: SELF_TYPE): SELF_TYPE { self }; };
class A2 inherits A3 { x(z: Int): Int { 1 / 1 }; };
class A3 inherits A4 { x(z: Int): Int { 1 + 1 }; };
class A4 inherits A1 { x(y: Int): Int { 1 }; };