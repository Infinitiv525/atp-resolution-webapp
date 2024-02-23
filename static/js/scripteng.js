const syntaxButton = document.getElementById("syntaxButton");
const syntaxContent = document.getElementById("syntaxContent");
const closeSyntaxButton = document.getElementById("closeSyntax");
const buttonGrid = document.querySelector('.button-grid');
const inputField = document.getElementById('text-input');
const inputForm = document.getElementById('inp-form');
const errorMessage = document.getElementById('errorMessage');
const copyMessage = document.getElementById("copy-message");
let isSyntaxVisible = false;


function tokenize(formula) {
    let tokens = [];
    let token = "";
    let i = 0;
    let is_name = false;

    while (i < formula.length) {
        if (formula[i] === ' ') {
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

function checkSyntax(input) {
    let tokens = tokenize(input);
    let vars = findVars(tokens);
    if (tokens.filter(token => token === '(').length !== tokens.filter(token => token === ')').length) {
        if (tokens.filter(token => token === '(').length > tokens.filter(token => token === ')').length) {
            return 1;
        } else {
            return 2;
        }
    }
    for (let i = 0; i < tokens.length - 1; i++) {
        let token = tokens[i];
        let next = tokens[i + 1];
        if (vars.includes(token) && (vars.includes(next) || next === '(')) {
            return 3;
        }
        if (operators.includes(token) && (operators.includes(next) && next !== 'not')) {
            return 4;
        }
        if (token === '(') {
            if ((operators.includes(next) && next !== 'not') || next === ')') {
                return 5;
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
                return 6;
            }
        }
        if (token === ')' && (next === 'not' || vars.includes(next) || next === '(')) {
            return 7;
        }
    }
    if (tokens.length > 0) {
        if (!vars.includes(tokens[tokens.length - 1]) && tokens[tokens.length - 1] !== ')') {
            return 8;
        }
        if ((operators.includes(tokens[0]) && tokens[0] !== 'not') || tokens[0] === ')') {
            return 9;
        }
    }
    return 0;
}

function handleInput() {
    var userInput = inputField.value;
    var isValidSyntax = checkSyntax(userInput);
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
    "not": ["!", "¬", "neg", "-", "~", "NOT", "Not"],
    "nand": ["↑", "⊼", "NAND", "Nand"],
    "nor": ["↓", "⊽", "NOR", "Nor"],
    "nimply": ["NIMPLY", "Nimply"],
    "xor": ["↮", "⊻", "^^", "^", "⊕", "nequiv", "neq", "NEQUIV", "NEQ", "EXOR", "XOR", "EOR", "Xor"],
    "and": ["·", "*", "&&", "&", "∧", "AND", "And", "land", "wedge"],
    "or": ["||", "|", "∨", "+", "OR", "Or", "lor", "vee"],
    "imply": ["→", "=>", ">", "⇒", "IMPLY", "Imply", "Rightarrow", "rightarrow"],
    "equiv": ["↔", "<=>", "<>", "<->", "⇔", "⊙", "vtt", "iff", "xnor", "EQUIV", "XNOR", "EQ", "Equiv", "Eq", "Xnor", "Leftrightarrow", "leftrightarrow"]
};
const operators = ['not', 'nand', 'nor', 'nimply', 'xor', 'and', 'or', 'imply', 'equiv'];

if (inputField) {
    inputField.addEventListener('input', handleInput);
    inputField.addEventListener('focus', handleInput);
}

//Local storage Load
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

//Local storage Save
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

        button.innerText = "Resolution tree";
    } else {
        treeContent.style.display = "block";
        tableContent.style.display = "none";

        button.innerText = "Resolution table";
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

        var userInput = inputField.value;
        var isValidSyntax = checkSyntax(userInput);

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
            inputField.value += symbol;
            inputField.focus();
        }
    });
}

if (inputField) {
    inputField.addEventListener('blur', function () {
        var userInput = inputField.value;
        var isValidSyntax = checkSyntax(userInput);
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
                    error = "Missing ')' parenthesis";
                    break;
                case 2:
                    error = "Missing '(' parenthesis";
                    break;
                case 3:
                    error = "Variable must be followed by a binary operator or ')'";
                    break;
                case 4:
                    error = "Operator cannot be followed by another binary operator";
                    break;
                case 5:
                    error = "'(' cannot be followed by a binary operator or ')'";
                    break;
                case 6:
                    error = "Unmatched parenthesis";
                    break;
                case 7:
                    error = "')' must be followed by a binary operator or ')'";
                    break;
                case 8:
                    error = "Formula must end with variable or ')'";
                    break;
                case 9:
                    error = "Formula cannot begin with binary operator or ')'";
                    break;
                default:
                    error = "Syntax error";
                    break;
            }
            errorMessage.textContent = error;
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

        localStorage.setItem('currentTheme', selectedTheme);
    });
});

document.addEventListener("DOMContentLoaded", function () {
    var checkbox = document.querySelector('.toggle input[type="checkbox"]');
    var treeContainer = document.getElementById('resolution-tree');
    var tableContainer = document.getElementById('resolution-table');

    checkbox.addEventListener('change', function () {
        if (checkbox.checked) {
            treeContainer.style.display = 'block';
            tableContainer.style.display = 'none';
        } else {
            treeContainer.style.display = 'none';
            tableContainer.style.display = 'block';
        }
    });
});

const divider = document.getElementById('divider');
const leftPanel = document.querySelector('.left-panel');
const rightPanel = document.querySelector('.right-panel');

let isResizing = false;

divider.addEventListener('mousedown', function (e) {
    isResizing = true;
    document.addEventListener('mousemove', resize);
    document.addEventListener('mouseup', () => {
        isResizing = false;
        document.removeEventListener('mousemove', resize);
    });
});

function resize(e) {
    if (isResizing) {
        const offsetLeft = e.clientX - leftPanel.getBoundingClientRect().left;
        const totalWidth = leftPanel.offsetWidth + rightPanel.offsetWidth;
        const leftWidthPercentage = (offsetLeft / totalWidth) * 100;
        leftPanel.style.flex = `${leftWidthPercentage}%`;
        rightPanel.style.flex = `${100 - leftWidthPercentage}%`;
    }
}

function checkEmptyDiv() {
    let outputDiv = document.getElementById('output-text');
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