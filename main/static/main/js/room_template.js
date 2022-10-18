room_name = JSON.parse(document.querySelector('#json_room_name').textContent)
room_name = room_name.toUpperCase()

twitch_login = JSON.parse(document.querySelector('#json_twitch_login').textContent)

streamer_mode = false

room_socket = new WebSocket('ws://' + window.location.host + '/ws/room/' + room_name)

room_socket.onmessage = function(e) {
  var data = JSON.parse(e.data)
  console.log(data)

  switch (data['action']) {
    case 'set_state':
      set_state(data)
      break
    case 'add_clue':
      add_clue(data['user_name'])
      break
    case 'add_user':
      console.log('YEY')
      row = add_user(data)
      update_table(row)
      break
    case 'show_table':
      show_result(data)
      break
    case 'change_like_count':
      change_like_count(data)
      break
    default:
      break
  }
}

room_socket.onclose = function(e) {
  console.log('The socket closed unexpectadly or expectadly')

  document.querySelector('.popup-body').innerHTML = 'Отключение от сервера'
  popup_redirect = '/'
  popup_modal.style.display = "block"
}

document.querySelector('#game_input_submit').onclick = function(e) {
  var game_input = document.querySelector('#game_input')
  var word = game_input.value.toLowerCase()
  // alert(10)
  room_socket.send(JSON.stringify({
    'action': 'handle_word',
    'word': word,
  }))
  game_input.value = ''
  document.querySelector('#game_input_form').style.display = 'none'
}



function set_state(data) {
  // start round
  if (data['set_state'] == 'start_round') {
    document.querySelector('#game_input_form').style.display = 'none'
    document.querySelector('#clues').innerHTML = ''
    document.querySelector('#crashed_clues').innerHTML = ''

    // display game_content and show the game form if needed
    if (streamer_mode == true) {
      document.querySelector("#game_content").innerHTML = `
          Загаданное слово будет отгадывать ${data['guesser_name']}.
          <br> В ожидании подсказок...`
    }
    else if (data['guesser_name'] == twitch_login) {
      document.querySelector("#game_content").innerHTML = `<font color="red">Вы будете угадывать в этом раунде.</font>
          <br>В ожидании подсказок...`
    }
    else {
      document.querySelector("#game_content").innerHTML = `
          Загаданное слово <b>${data['word'].toUpperCase()}</b>
          будет отгадывать ${data['guesser_name']}.
          <br> <b>Введите подсказку - одно слово</b>`
      document.querySelector('#game_input').placeholder = 'Введите подсказку'
      document.querySelector('#game_input_form').style.display = 'block'
    }
  }

  // start guessing
  if (data['set_state'] == 'start_guessing') {
    document.querySelector('#game_input_form').style.display = 'none'
    document.querySelector('#clues').innerHTML = ''
    show_clues(data)
    show_crashed_clues(data)

    if (streamer_mode == true) {
      document.querySelector("#game_content").innerHTML = `Угадывает ${data['guesser_name']}. В ожидании...`
    }
    else if (data['guesser_name'] == twitch_login) {
      document.querySelector("#game_content").innerHTML = `
          Введите свою догадку... <br>
          У вас только одна попытка, так что не торопитесь!`
      document.querySelector('#game_input').placeholder = 'Введите слово'
      document.querySelector('#game_input_form').style.display = 'block'
    } else {
      document.querySelector("#game_content").innerHTML = `Угадывает ${data['guesser_name']}. В ожидании...`
    }
  }

  if (data['set_state'] == 'show_result') {
    document.querySelector('#game_input_form').style.display = 'none'
    document.querySelector('#crashed_clues').innerHTML = ''
    show_crashed_clues(data, show_word=true)
    if (streamer_mode == true) {
      if (data['guess'] == data['word']) {
        new Audio('static/main/sounds/correct.mp3').play()
      } else {
        new Audio('static/main/sounds/wrong.mp3').play()
      }
    }
    game_content = ``
    if (data['guesser_name'] == twitch_login) {
      if (data['guess'] == data['word']) {
        game_content = `Вы ввели <b>${data['guess'].toUpperCase()}</b>, и это <font color="green"><b>ВЕРНО</b></font>`
      } else {
        if (data['guess'] != '') {
          game_content = `Вы ввели <b>${data['guess'].toUpperCase()}</b>, и это <font color="red"><b>НЕВЕРНО</b></font>
              <br> Загаданное слово <b>${data['word'].toUpperCase()}</b>`
        } else {
          game_content = `Вы ничего не ввели
              <br> Загаданное слово <b>${data['word'].toUpperCase()}</b>`
        }
      }
    } else {
      if (data['guess'] == data['word']) {
        game_content = `${data['guesser_name']} ввел <b>${data['guess'].toUpperCase()}</b>, и это <font color="green"><b>ВЕРНО</b></font>`
      } else {
          if (data['guess'] != '') {
            game_content = `${data['guesser_name']} ввел <b>${data['guess'].toUpperCase()}</b>, и это <font color="red"><b>НЕВЕРНО</b></font>
                <br> Загаданное слово <b>${data['word'].toUpperCase()}</b>`
          } else {
            game_content = `${data['guesser_name']} ничего не ввел
                <br> Загаданное слово <b>${data['word'].toUpperCase()}</b>`
          }
      }
    }
    document.querySelector("#game_content").innerHTML = game_content
  }
}


function like_onclick(e) {
  if (streamer_mode == true) {
    return
  }
  user_name = e.dataset.username
  if (twitch_login == user_name) {
    return
  }
  like_button = document.querySelector(`.like_heart[data-username="${user_name}"]`)
  if (like_button.classList.contains('unliked')) {
    like_button.classList.remove('unliked')
    like_button.classList.add('liked')
  } else {
    like_button.classList.remove('liked')
    like_button.classList.add('unliked')
  }
  room_socket.send(JSON.stringify({
    'action': 'add_like',
    'user_name': user_name,
  }))
}

function add_clue(user_name, clue='', crash=false, like_button=false) {
  var inner = ''
  inner += `
      <div id="" class="clue_card">
        <div class="author_clue">
          <div class="author">
            ${user_name}
          </div>
          <div class="clue">
            ${clue}
          </div>
        </div>`
  if (like_button == true) {
    inner += `
        <div>
          <div class="unliked like_heart" data-username="${user_name}">♥</div>
          <div class="like_count" data-username="${user_name}" onclick="like_onclick(this)">0</div>
        </div>`
  }
  inner += '</div>'

  document.querySelector('#clues').innerHTML += inner

  if (crash != false) {
    // for (user_name in ) {
    //   document.querySelector('input[data-username=""]')
    // }
  }
}

function show_clues(data) {
  for (var word in data['clues']) {
    user_name = data['clues'][word][0]
    add_clue(user_name, word, false, true)
  }
}

function show_crashed_clues(data, show_word=false) {
  for (var word in data['crashed_clues']) {
    var inner = ''
    inner += `<div style="margin-top: 10px;"> ${(show_word == false) ? '???' : word} </div>`
    inner += '<div class="crashed_clue_group">'
    for (var i in data['crashed_clues'][word]) {
      user_name = data['crashed_clues'][word][i]
      inner += `<div class="crashed_clue_card"> ${user_name} </div>`
    }
    inner += '</div>'
    document.querySelector('#crashed_clues').innerHTML += inner
  }
}



function add_user(data) {
  row = `
  <tr>
    <td>${data['user_name']}</td>
    <td>${data['score']}</td>
    <td>${data['clues']-data['crashes']}/${data['clues']}</td>
    <td>${data['right_guesses']}/${data['guesses']}</td>
  </tr>`
  return row
}

function update_table(rows) {
  var table = document.querySelector('#game_results').innerHTML
  table = table.slice(0, -16) + rows + `
    </tbody>
  </table>`
  document.querySelector('#game_results').innerHTML = table
}


function show_result(data) {
  document.querySelector('#game_results').innerHTML = `
  <table>
    <thead>
      <tr>
        <th>Игрок</th>
        <th>Счет</th>
        <th>Подсказок</th>
        <th>Угадываний</th>
      </tr>
    </thead>
  </table>
  `
  var items = Object.keys(data['table']).map(
    (key) => { return [key, data['table'][key]] })

  console.log(items)
  items.sort(
    (first, second) => { return -(parseInt(first[1]['score']) - parseInt(second[1]['score'])) }
  )
  for (var i in items) {
    row = add_user(items[i][1])
    update_table(row)
  }
}

function change_like_count(data) {
  user_name = data['user_name']
  like_count = document.querySelector(`.like_count[data-username="${user_name}"]`)
  if (like_count !== null) {
    like_count.innerHTML = parseInt(like_count.innerHTML) + data['change_type']
  }
}
