function removeDependency(url)
{
  const csrftoken = document.querySelector('[name=csrfmiddlewaretoken]').value;

  $.ajax({
    method: 'DELETE',
    headers: {'X-CSRFToken': csrftoken},
    url: url,
    success: function(response) {
	    child = url.match('[0-9]+$');
		$('li#' + child).fadeOut(300);
    }
  });
}
