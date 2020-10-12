const ben = require('ben-jsutils');
const he = require('he');

const path = './Code2/';

ben.fs.listDir(path).then(titles => {
    console.log(titles);
    titles.forEach((t, ti) => {
        ben.fs.readFile(path+t).then(text => {
            // console.log(text);
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
            // const textarray = text.split('id="');
            // const sanaray = textarray.map(te => {
            //     if (te[0] === 'i' && te[1] === 'd') {
            //         return te.slice(40);
            //     }
            //     return te;
            // });

            let lines = text.split("\n");
            let newstr = lines.filter(l => !l.startsWith('<!--')).map(he.decode).join('\n');
            // console.log(strip_html_tags(newstr));
            // console.log(sanaray);
            // console.log(text);
            ben.fs.writeFile(path+t, strip_html_tags(newstr));
        });
    });
});

function strip_html_tags(str) {
   if ((str===null) || (str===''))
       return false;
  else
   str = str.toString();
  return str.replace(/<[^>]*>/g, '');
}

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