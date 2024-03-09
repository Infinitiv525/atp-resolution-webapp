const syntaxButton = document.getElementById("syntaxButton");
const syntaxContent = document.getElementById("syntaxContent");
const closeSyntaxButton = document.getElementById("closeSyntax");
const buttonGrid = document.querySelector('.button-grid');
const inputField = document.getElementById('text-input');
const inputForm = document.getElementById('inp-form');
const errorMessage = document.getElementById('errorMessage');
const copyMessage = document.getElementById("copy-message");
let isSyntaxVisible = false;
const htmlLang = document.documentElement.lang;


function tokenize(formula) {
    let tokens = [];
    let token = "";
    let i = 0;
    let is_name = false;

    while (i < formula.length) {
        if (formula[i] === ' ' || formula[i] === '\n') {
            is_name = false;
            if (token !== "") {
                tokens.push(token);
                token = "";
            }
            i++;
            continue;
        }
        if (formula[i] === '(' || formula[i] === ')') {
            is_name = false;
            if (token !== "") {
                tokens.push(token);
                token = "";
            }
            tokens.push(formula[i]);
            i++;
            continue;
        }
        let is_operator = false;
        if (!is_name) {
            for (let op of operators) {
                if (formula.slice(i, i + op.length) === op) {
                    tokens.push(op);
                    i += op.length;
                    is_operator = true;
                    break;
                }
                let isalt = false;
                for (let alt of operator_dic[op]) {
                    if (formula.slice(i, i + alt.length) === alt) {
                        tokens.push(op);
                        i += alt.length;
                        is_operator = true;
                        isalt = true;
                        break;
                    }
                }
                if (isalt) {
                    break;
                }
            }
        }
        if (!is_operator) {
            if (formula[i] !== '\\') {
                is_name = true;
                token += formula[i];
            }
            i++;
        }
    }
    if (token !== "") {
        tokens.push(token);
    }
    return tokens;
}

function findVars(formula) {
    let vars = [];

    for (let elm of formula) {
        if (!operators.includes(elm) && !vars.includes(elm) && elm != "(" && elm != ")") {
            vars.push(elm);
        }
    }
    return vars.sort();
}

function isDimacs(text){
    let pattern = /^p\s+cnf\s+\d+\s+\d+/;
    let regex = new RegExp(pattern);

    let lines = text.split('\n');

    if (!regex.test(lines[0])) return -1;

    let match = lines[0].match(/(\d+)\s+(\d+)/);

    let numClauses = parseInt(match[2]);
    let actualNumClauses = text.split('\n').slice(1).filter(line => line.trim() !== '').length;

    if(numClauses < actualNumClauses) return 10;
    if(numClauses > actualNumClauses) return 11;

    let numVariables = parseInt(match[1]);

    for (let i = 1; i < lines.length; i++) {
        let clause = lines[i].trim().split(' ');
        for (let j = 0; j < clause.length; j++) {
            if (clause[j] === '') continue;
            if (isNaN(parseInt(clause[j]))) return 12;
            if (Math.abs(parseInt(clause[j])) > numVariables) return 13;
            if (j === clause.length -1  && parseInt(clause[j]) !== 0) return 14;
        }
    }

    return 0;
}

function checkSyntax(input) {
    let dimacs = isDimacs(input);
    if (dimacs !== -1) return dimacs;
    let tokens = tokenize(input);
    let vars = findVars(tokens);
    if (tokens.filter(token => token === '(').length !== tokens.filter(token => token === ')').length) {
        if (tokens.filter(token => token === '(').length > tokens.filter(token => token === ')').length) {
            return { errorCode: 1, position: tokens.indexOf('(')};
        } else {
            return { errorCode: 2, position: tokens.indexOf(')') };
        }
    }
    for (let i = 0; i < tokens.length - 1; i++) {
        let token = tokens[i];
        let next = tokens[i + 1];
        if (vars.includes(token) && (vars.includes(next) || next === '(' || next === 'not')) {
            return { errorCode: 3, position: i + 1};
        }
        if (operators.includes(token) && ((operators.includes(next) && next !== 'not') || next === ")")) {
            return { errorCode: 4, position: i + 1};
        }
        if (token === '(') {
            if ((operators.includes(next) && next !== 'not') || next === ')') {
                return { errorCode: 5, position: i + 1 };
            }
            let j = i + 1;
            let brackets = 0;
            while (j <= tokens.length) {
                if (tokens[j] === ')') {
                    if (brackets === 0) {
                        break;
                    } else {
                        brackets--;
                    }
                }
                if (tokens[j] === '(') {
                    brackets++;
                }
                j++;
            }
            if (j === tokens.length + 1) {
                return { errorCode: 6, position: i + 1};
            }
        }
        if (token === ')' && (next === 'not' || vars.includes(next) || next === '(')) {
            return { errorCode: 7, position: i + 1};
        }
    }
    if (tokens.length > 0) {
        if (!vars.includes(tokens[tokens.length - 1]) && tokens[tokens.length - 1] !== ')') {
            return { errorCode: 8, position: tokens.length - 1 };
        }
        if ((operators.includes(tokens[0]) && tokens[0] !== 'not') || tokens[0] === ')') {
            return { errorCode: 9, position: 0 };
        }
    }
    return { errorCode: 0, position: -1 };
}

function handleInput() {
    var userInput = inputField.value;
    localStorage.setItem('textInputValue', document.getElementById('text-input').value);
    var isValidSyntax = checkSyntax(userInput).errorCode;
    errorMessage.style.display = 'none';

    if (isValidSyntax === 0) {
        inputField.style.borderColor = '';
        inputForm.style.borderColor = '';
        inputField.style.outline = '';
    } else {
        inputField.style.borderColor = 'red';
        inputForm.style.borderColor = 'red';
        inputField.style.outline = '1px solid red';
        inputField.style.borderRadius = '5px';
    }
}

const operator_dic = {
    "not": ["¬", "!", "-", "~", "NOT", "Not", "Neg", "NEG", "neg"],
    "nand": ["↑", "⊼", "NAND", "Nand", "uparrow"],
    "nor": ["↓", "⊽", "NOR", "Nor", "downarrow"],
    "nimplies": ["⇏", "NIMPLY", "Nimply", "nimply", "NIMPLIES", "Nimplies", "nRightarrow"],
    "xor": ["⊕", "↮", "⊻", "^^", "^", "nequiv", "neq", "NEQUIV", "NEQ", "EXOR", "XOR", "EOR", "Xor", "oplus"],
    "and": ["·", "*", "&&", "&", "∧", "AND", "And", "land", "wedge"],
    "or": ["||", "|", "∨", "+", "OR", "Or", "lor", "vee"],
    "implies": ["⇒", "→", "=>", ">", "IMPLY", "Imply", "rightarrow", "imply", "Implies", "IMPLIES", "Rightarrow"],
    "equiv": ["↔", "<=>", "<>", "<->", "⇔", "⊙", "vtt", "iff", "xnor", "EQUIV", "XNOR", "EQ", "Equiv", "Eq", "Xnor", "Leftrightarrow", "leftrightarrow"]
};
const operators = ['not', 'nand', 'nor', 'nimplies', 'xor', 'and', 'or', 'implies', 'equiv'];

if (inputField) {
    inputField.addEventListener('input', handleInput);
    inputField.addEventListener('focus', handleInput);
}

//Local storage load
document.addEventListener('DOMContentLoaded', function () {
    const textInput = document.getElementById('text-input');
    const savedTextValue = localStorage.getItem('textInputValue');
    if (textInput === null) {
        return;
    }
    if (savedTextValue) {
        textInput.value = savedTextValue;
    }
    const radioInputs = document.querySelectorAll('input[type="radio"]');
    const savedRadioValue = localStorage.getItem('selectedRadio');
    if (savedRadioValue) {
        radioInputs.forEach(input => {
            if (input.value === savedRadioValue) {
                input.checked = true;
            }
        });
    } else {
        document.getElementById('option1').checked = true;
    }
    const checkbox = document.getElementById('reduced');
    const savedCheckboxValue = localStorage.getItem('checkboxValue');
    if (savedCheckboxValue === 'true') {
        checkbox.checked = true;
    }
    document.getElementById("fontSizeSelect");
    var selectElement = document.getElementById("fontSizeSelect");
    var savedFontSize = localStorage.getItem("fontSize");
    if (savedFontSize) {
        selectElement.value = savedFontSize;
        changeFontSize();
    }
});

//Local Storage Save
if (inputForm) {
    inputForm.addEventListener('change', function () {
        localStorage.setItem('textInputValue', document.getElementById('text-input').value);
        const selectedRadio = document.querySelector('input[name="option"]:checked');
        if (selectedRadio) {
            localStorage.setItem('selectedRadio', selectedRadio.value);
        }
        localStorage.setItem('checkboxValue', document.getElementById('reduced').checked);
    });
}

document.addEventListener("DOMContentLoaded", function () {
    toggleOptions();
    checkEmptyDiv();
});

function toggleOptions() {
    var button = document.getElementById("switch-button");
    var treeContent = document.getElementById("resolution-tree");
    var tableContent = document.getElementById("resolution-table");

    if (button === null) {
        return;
    }
    if (treeContent.style.display !== "none") {
        treeContent.style.display = "none";
        tableContent.style.display = "block";
        if (htmlLang === "sk") button.innerText = "Rezolučný strom";
        else button.innerText = "Resolution tree";
    } else {
        treeContent.style.display = "block";
        tableContent.style.display = "none";

        if (htmlLang === "sk") button.innerText = "Rezolučná tabuľka";
        else button.innerText = "Resolution table";
    }
}

function changeFontSize() {
    var selectElement = document.getElementById("fontSizeSelect");
    var selectedValue = selectElement.options[selectElement.selectedIndex].text;

    document.getElementById("output-text").style.fontSize = selectedValue;
    document.getElementById("text-input").style.fontSize = selectedValue;
    localStorage.setItem('fontSize', selectElement.value);
}

function copyToClipboardTree() {
    var copyText = document.getElementById("latex-tree");
    if (navigator.clipboard) {
        copyText.select();
        navigator.clipboard.writeText(copyText.value)
            .then(function () {
                console.log('Text successfully copied to clipboard');
            })
            .catch(function (err) {
                console.error('Unable to copy text to clipboard', err);
            });
    } else {
        var tempTextArea = document.createElement('textarea');
        tempTextArea.value = copyText.value;
        document.body.appendChild(tempTextArea);
        tempTextArea.select();
        document.execCommand('copy');
        document.body.removeChild(tempTextArea);
    }
    copyMessage.style.display = 'block';
    copyMessage.style.right = '40px';
    copyMessage.style.left = '';
    setTimeout(function () {
        copyMessage.style.display = 'none';
    }, 2000);
}

function copyToClipboardTable() {
    var copyText = document.getElementById("latex-table");
    if (navigator.clipboard) {
        copyText.select();
        navigator.clipboard.writeText(copyText.value)
            .then(function () {
                console.log('Text successfully copied to clipboard');
            })
            .catch(function (err) {
                console.error('Unable to copy text to clipboard', err);
            });
    } else {
        var tempTextArea = document.createElement('textarea');
        tempTextArea.value = copyText.value;
        document.body.appendChild(tempTextArea);
        tempTextArea.select();
        document.execCommand('copy');
        document.body.removeChild(tempTextArea);
    }
    copyMessage.style.display = 'block';
    copyMessage.style.right = '185px';
    copyMessage.style.left = '';
    setTimeout(function () {
        copyMessage.style.display = 'none';
    }, 2000);
}

function copyToClipboardOutput() {
    var copyText = document.getElementById("latex-output");
    if (navigator.clipboard) {
        copyText.select();
        navigator.clipboard.writeText(copyText.value)
            .then(function () {
                console.log('Text successfully copied to clipboard');
            })
            .catch(function (err) {
                console.error('Unable to copy text to clipboard', err);
            });
    } else {
        var tempTextArea = document.createElement('textarea');
        tempTextArea.value = copyText.value;
        document.body.appendChild(tempTextArea);
        tempTextArea.select();
        document.execCommand('copy');
        document.body.removeChild(tempTextArea);
    }
    copyMessage.style.display = 'block';
    copyMessage.style.left = '10px';
    copyMessage.style.right = '';
    setTimeout(function () {
        copyMessage.style.display = 'none';
    }, 2000);
}

if (inputForm) {
    inputForm.addEventListener('submit', function (event) {
        event.preventDefault();

        localStorage.setItem('textInputValue', document.getElementById('text-input').value);
        const selectedRadio = document.querySelector('input[name="option"]:checked');
        if (selectedRadio) {
            localStorage.setItem('selectedRadio', selectedRadio.value);
        }
        localStorage.setItem('checkboxValue', document.getElementById('reduced').checked);

        var userInput = inputField.value;
        var isValidSyntax = checkSyntax(userInput).errorCode;

        if (isValidSyntax !== 0) {
            inputField.style.borderColor = 'red';
            return false;
        }
        this.submit();
    });
}

if (buttonGrid) {
    buttonGrid.addEventListener('click', (e) => {
        const symbol = e.target.getAttribute('data-symbol');
        if (symbol) {
            const startPos = inputField.selectionStart;
            const endPos = inputField.selectionEnd;

            const textBefore = inputField.value.substring(0, startPos);
            const textAfter = inputField.value.substring(endPos, inputField.value.length);

            inputField.value = textBefore + symbol + textAfter;

            // Adjust cursor position after inserting the symbol
            inputField.selectionStart = startPos + symbol.length;
            inputField.selectionEnd = startPos + symbol.length;

            inputField.focus();
        }
    });
}

if (inputField) {
    inputField.addEventListener('blur', function () {
        let userInput = inputField.value;
        let result = checkSyntax(userInput);
        let isValidSyntax = result.errorCode;
        inputField.style.outline = '';
        if (isValidSyntax === 0) {
            errorMessage.style.display = 'none';
            inputField.style.borderColor = '';
        } else {
            let error;
            errorMessage.style.display = 'block';
            inputField.style.borderColor = 'red';
            switch (isValidSyntax) {
                case 1:
                    if (htmlLang === "sk") error = "Chýbajúce ')' zátvorky";
                    else error = "Missing ')' parenthesis";
                    break;
                case 2:
                    if (htmlLang === "sk") error = "Chýbajúce '(' zátvorky";
                    else error = "Missing '(' parenthesis";
                    break;
                case 3:
                    if (htmlLang === "sk") error = "Za premennou musí nasledovať binárny operátor alebo ')'";
                    else error = "Variable must be followed by a binary operator or ')'";
                    break;
                case 4:
                    if (htmlLang === "sk") error = "Za operátorom nesmie nasledovať ďalší binárny operátor alebo ')'";
                    else error = "Operator cannot be followed by another binary operator or ')'";
                    break;
                case 5:
                    if (htmlLang === "sk") error = "Za '(' nesmie nasledovať binárny operátor alebo ')'";
                    else error = "'(' cannot be followed by a binary operator or ')'";
                    break;
                case 6:
                    if (htmlLang === "sk") error = "Neuzatvorená zátvorka";
                    else error = "Unmatched parenthesis";
                    break;
                case 7:
                    if (htmlLang === "sk") error = "Za ')' musí nasledovať binárny operátor alebo ')'";
                    else error = "')' must be followed by a binary operator or ')'";
                    break;
                case 8:
                    if (htmlLang === "sk") error = "Formula musí končiť premennou alebo ')'";
                    else error = "Formula must end with variable or ')'";
                    break;
                case 9:
                    if (htmlLang === "sk") error = "Formula nesmie začínať binárnym operátorom alebo ')'";
                    else error = "Formula cannot begin with binary operator or ')'";
                    break;
                case 10:
                    if (htmlLang === "sk") error = "Príliš veľa klauzúl v DIMACS";
                    else error = "Too many clauses in DIMACS";
                    break;
                case 11:
                    if (htmlLang === "sk") error = "Príliš málo klauzúl v DIMACS";
                    else error = "Too few clauses in DIMACS";
                    break;
                case 12:
                    if (htmlLang === "sk") error = "Klauzuly v DIMACS môžu obsahovať len čísla";
                    else error = "Clauses in DIMACS can only contain integers";
                    break;
                case 13:
                    if (htmlLang === "sk") error = "Príliš veľa premenných v DIMACS";
                    else error = "Too many variables in DIMACS";
                    break;
                case 14:
                    if (htmlLang === "sk") error = "Klauzula musí končiť nulou";
                    else error = "A clause must end with 0";
                    break;
                default:
                    if (htmlLang === "sk") error = "Chyba syntaxe";
                    else error = "Syntax error";
                    break;
            }
            let tokens = tokenize(inputField.value);
            errorMessage.textContent = error + "; token "+ (result.position+1) + ': "' + tokens[result.position] + '"';
        }
    });
}

document.addEventListener('DOMContentLoaded', function () {
    const themeSelect = document.getElementById('theme-select');
    const body = document.body;
    const containers = document.getElementsByClassName("container");
    const svgElement = document.getElementsByTagName("svg")[0];
    const clickButtons = document.getElementsByClassName("click-button");
    const tables = document.getElementsByTagName("table");
    const ths = document.getElementsByTagName("th");
    const tds = document.getElementsByTagName("td");
    const input = document.getElementById("text-input");
    const buttons = document.getElementsByClassName("button");
    const inputs = document.getElementsByTagName("input");
    const imgs = document.getElementsByClassName("sym");
    const divider = document.getElementById('divider');
    const selects = document.getElementsByTagName('select');
    const checkmarks = document.getElementsByClassName("checkmark");
    const checkmarks2 = document.getElementsByClassName("checkmark2");

    const themes = ['morning', 'noon', 'sunset', 'midnight', 'matrix'];

    const savedTheme = localStorage.getItem('currentTheme');
    const defaultTheme = savedTheme && themes.includes(savedTheme) ? savedTheme : themes[0];

    body.classList.add(defaultTheme);
    themeSelect.value = defaultTheme;
    if (svgElement) svgElement.classList.add(defaultTheme);
    if (input) input.classList.add(defaultTheme);
    if (divider) divider.classList.add(defaultTheme);

    for (let container of containers) {
        container.classList.add(defaultTheme);
    }

    for (let button of clickButtons) {
        button.classList.add(defaultTheme);
    }

    for (let table of tables) {
        table.classList.add(defaultTheme);
    }

    for (let th of ths) {
        th.classList.add(defaultTheme);
    }

    for (let td of tds) {
        td.classList.add(defaultTheme);
    }

    for (let button of buttons) {
        button.classList.add(defaultTheme);
    }

    for (let input of inputs) {
        input.classList.add(defaultTheme);
    }

    for (let img of imgs) {
        if (defaultTheme === "matrix") img.src = "static/img/" + img.alt + "-matrix.png";
        else if (defaultTheme === "midnight") img.src = "static/img/" + img.alt + "-midnight.png";
        else img.src = "static/img/" + img.alt + ".png";
    }

    for (let select of selects) {
        select.classList.add(defaultTheme);
    }

    for (let checkmark of checkmarks){
        checkmark.classList.add(defaultTheme);
    }
    for (let checkmark2 of checkmarks2){
        checkmark2.classList.add(defaultTheme);
    }

    themeSelect.addEventListener('change', function () {
        const selectedTheme = themeSelect.value;

        // Remove the current theme
        body.classList.remove(...themes);
        if (svgElement) svgElement.classList.remove(...themes);
        if (input) input.classList.remove(...themes);
        if (divider) divider.classList.remove(...themes);

        // Apply the selected theme
        body.classList.add(selectedTheme);
        if (svgElement) svgElement.classList.add(selectedTheme);
        if (input) input.classList.add(selectedTheme);
        if (divider) divider.classList.add(selectedTheme);

        for (let container of containers) {
            container.classList.remove(...themes);
            container.classList.add(selectedTheme);
        }

        for (let button of clickButtons) {
            button.classList.remove(...themes);
            button.classList.add(selectedTheme);
        }

        for (let table of tables) {
            table.classList.remove(...themes);
            table.classList.add(selectedTheme);
        }

        for (let th of ths) {
            th.classList.remove(...themes);
            th.classList.add(selectedTheme);
        }

        for (let td of tds) {
            td.classList.remove(...themes);
            td.classList.add(selectedTheme);
        }

        for (let button of buttons) {
            button.classList.remove(...themes);
            button.classList.add(selectedTheme);
        }

        for (let input of inputs) {
            input.classList.remove(...themes);
            input.classList.add(selectedTheme);
        }

        for (let img of imgs) {
            if (selectedTheme === "matrix") img.src = "static/img/" + img.alt + "-matrix.png";
            else if (selectedTheme === "midnight") img.src = "static/img/" + img.alt + "-midnight.png";
            else img.src = "static/img/" + img.alt + ".png";
        }

        for (let select of selects) {
            select.classList.remove(...themes);
            select.classList.add(selectedTheme);
        }

        for (let checkmark of checkmarks){
            checkmark.classList.remove(...themes);
            checkmark.classList.add(selectedTheme);
        }

        for (let checkmark2 of checkmarks2){
            checkmark2.classList.remove(...themes);
            checkmark2.classList.add(selectedTheme);
        }

        localStorage.setItem('currentTheme', selectedTheme);
    });
});

document.addEventListener("DOMContentLoaded", function () {
    var checkbox = document.querySelector('.toggle input[type="checkbox"]');
    var treeContainer = document.getElementById('resolution-tree');
    var tableContainer = document.getElementById('resolution-table');

    if (checkbox) {
        checkbox.addEventListener('change', function () {
            if (checkbox.checked) {
                treeContainer.style.display = 'block';
                tableContainer.style.display = 'none';
            } else {
                treeContainer.style.display = 'none';
                tableContainer.style.display = 'block';
            }
        });
    }
});

const divider = document.getElementById('divider');
const leftPanel = document.querySelector('.left-panel');
const rightPanel = document.querySelector('.right-panel');

let isResizing = false;

if (divider) {
    divider.addEventListener('mousedown', function (e) {
        isResizing = true;
        document.addEventListener('mousemove', resize);
        document.addEventListener('mouseup', () => {
            isResizing = false;
            document.removeEventListener('mousemove', resize);
        });
    });
}

function resize(e) {
    if (isResizing) {
        let leftWidthPercentage;
        if (window.innerWidth < 600) {
            const offsetTop = e.clientY - leftPanel.getBoundingClientRect().top;
            const totalHeight = leftPanel.offsetHeight + rightPanel.offsetHeight;
            leftWidthPercentage = (offsetTop / totalHeight) * 100;
        }
        else {
            const offsetLeft = e.clientX - leftPanel.getBoundingClientRect().left;
            const totalWidth = leftPanel.offsetWidth + rightPanel.offsetWidth;
            leftWidthPercentage = (offsetLeft / totalWidth) * 100;
        }
        leftPanel.style.flex = `${leftWidthPercentage}%`;
        rightPanel.style.flex = `${100 - leftWidthPercentage}%`;
    }
}

function checkEmptyDiv() {
    let outputDiv = document.getElementById('output-text');
    if (!outputDiv) return;
    let containers = document.getElementsByClassName('container');
    let hideButtons = document.getElementsByClassName('hide');
    if (outputDiv.innerHTML.trim() === '') {
        for (let container of containers) {
            container.style.display = 'none';
        }
        for (let hideButton of hideButtons) {
            hideButton.style.display = 'none';
        }
    } else {
        for (let container of containers) {
            container.style.display = 'flex';
        }
        for (let hideButton of hideButtons) {
            hideButton.style.display = 'block';
        }
    }
}