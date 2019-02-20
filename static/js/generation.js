function getRandomInt(min, max) {
    min = Math.ceil(min);
    max = Math.floor(max);
    return Math.floor(Math.random() * (max - min + 1)) + min;
}


function gen() {
    for (var i = 0; i < 45; i++) {
        document.getElementById(i.toString()).value = getRandomInt(1, 4).toString();
    }
}

