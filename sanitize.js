const ben = require('ben-jsutils');

const path = './Code/';

ben.fs.listDir(path).then(titles => {
    titles.forEach((t, ti) => {
        ben.fs.readFile(path+t).then(text => {
            // console.log(i, text);
            // const idinds = getIndicesOf('id="id', text);
            // idinds.forEach(ii => {
            //     console.log(ii);
            //     text = text.slice(0, ii-1) + text.slice(ii+43);
            // });
            // let idind = text.indexOf('id="id');
            // while (idind > -1) {
            //     // console.log(idind);
            //     text = text.slice(0, idind-1) + text.slice(idind+43);
            //     idind = text.indexOf('id="id');
            // }
            const textarray = text.split('id="');
            const sanaray = textarray.map(te => {
                if (te[0] === 'i' && te[1] === 'd') {
                    return te.slice(40);
                }
                return te;
            });
            // console.log(sanaray);
            // console.log(text);
            ben.fs.writeFile(path+t, sanaray.join('')).then(console.log);
        });
    });
});

function getIndicesOf(searchStr, str, caseSensitive) {
    var searchStrLen = searchStr.length;
    if (searchStrLen == 0) {
        return [];
    }
    var startIndex = 0, index, indices = [];
    if (!caseSensitive) {
        str = str.toLowerCase();
        searchStr = searchStr.toLowerCase();
    }
    while ((index = str.indexOf(searchStr, startIndex)) > -1) {
        indices.push(index);
        startIndex = index + searchStrLen;
    }
    return indices;
}

var indices = getIndicesOf("le", "I learned to play the Ukulele in Lebanon.");
console.log(indices);
