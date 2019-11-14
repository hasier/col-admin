(function() {
    'use strict';
    window.addEventListener('load', function () {
        var todayIcons = document.querySelectorAll('i.today');
        if (todayIcons.length) {
            for (let todayIcon of todayIcons) {
                todayIcon.addEventListener('click', function() {
                    let input = this.closest('.date-input').querySelector('.datepicker');
                    let instance = M.Datepicker.getInstance(input);
                    instance.setDate(new Date());
                    instance._finishSelection();
                });
            }
        }
        var calendars = document.querySelectorAll('i.calendar');
        if (calendars.length) {
            for (var calendar of calendars) {
                calendar.addEventListener('click', function() {
                    let input = this.closest('.date-input').querySelector('.datepicker');
                    input.click();
                });
            }
        }
    });
})();
