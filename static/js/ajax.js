var province = document.getElementById('province');
var cities = document.getElementById('cities');
// var orderVia = document.getElementById('order_via');
// var predictButton = document.getElementById('predictButton');
var currentProvince, currentCity, currentOrder;
async function getData() {
  var xhttp = new XMLHttpRequest();
  xhttp.onreadystatechange = function () {
    if (this.readyState == 4 && this.status == 200) {
      var result = JSON.parse(this.responseText);
      var keys = Object.keys(result);
      for (index in keys) {
        var opt = document.createElement('option');
        opt.value = keys[index];
        opt.innerHTML = keys[index];
        province.appendChild(opt);
        }
        
        province.addEventListener('change', function handleChange(event) {
            cities.innerHTML = '';
            currentProvince = event.target.value;
            var first = document.createElement('option');
            first.innerHTML = 'Pilih Kota';
            cities.appendChild(first);
           console.log(event.target.value); // 👉️ get selected VALUE
             for (val in result[event.target.value]) {
               var opt = document.createElement('option');
               opt.value = result[event.target.value][val];
               opt.innerHTML = result[event.target.value][val];
               cities.appendChild(opt);
           }
        });

        cities.addEventListener('change', function handleChange(event) {
          console.log(event.target.value); // 👉️ get selected VALUE
          currentCity = event.target.value;
        });

        // orderVia.addEventListener('change', function handleChange(event) {
        //   console.log(event.target.value); // 👉️ get selected VALUE
        //   currentOrder = event.target.value;
        // });
        
     
    }
  };
  xhttp.open('GET', 'locations', true);
  xhttp.send();
}

getData();

async function postData() {

    let postObj = {
      province: currentProvince,
      city: currentCity,
      order_via: currentOrder,
    };
     let post = JSON.stringify(postObj);

  
     let xhr = new XMLHttpRequest();

     xhr.open('POST', '/classification', true);
     xhr.setRequestHeader('Content-type', 'application/json; charset=UTF-8');
     xhr.send(post);

     xhr.onload = function () {
       if (xhr.status === 200) {
         console.log(xhr.responseText);
       }
     };
}

// predictButton.addEventListener('click', function () {
//     postData();
// })
